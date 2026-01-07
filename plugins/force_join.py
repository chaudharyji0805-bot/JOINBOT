from collections import defaultdict
import time
import asyncio
from datetime import datetime, timedelta

from pyrogram.errors import UserNotParticipant
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatPermissions,
)

from database import group_settings, users, group_stats
from plugins.stats_tracker import inc_message, inc_force_action

WARN_COUNT = defaultdict(int)   # (chat_id, user_id) -> count
FORCE_WARNINGS = {}             # (chat_id, user_id) -> message_id
MAX_WARNINGS = 3


def valid_url(url: str) -> bool:
    return bool(url) and url.startswith("https://t.me/")


async def force_join_check(client, message, user=None):
    if not user:
        user = message.from_user
    
    print(f"DEBUG: Checking {user.id} in {message.chat.id}", flush=True) # debug
    
    chat = message.chat

    # basic checks
    if not user or not chat:
        print(f"DEBUG: Skipping - no user or chat", flush=True)
        return True
    
    # Convert enum to string for comparison
    chat_type = str(chat.type).replace("ChatType.", "").lower()
    print(f"DEBUG: Chat type: {chat_type}", flush=True)
    
    if chat_type not in ("group", "supergroup"):
        print(f"DEBUG: Skipping - not a group (type: {chat_type})", flush=True)
        return True
    
    # Ignore Admins
    try:
        # Check Authorized users first
        from plugins.aauth import is_authorized
        if await is_authorized(user.id):
            print(f"DEBUG: User {user.id} is AUTHORIZED (AAUTH). Skipping Force Join.", flush=True)
            return True

        mem = await client.get_chat_member(chat.id, user.id)
        status_str = str(mem.status).replace("ChatMemberStatus.", "").lower()
        
        if status_str in ("administrator", "owner", "creator"):
            print(f"DEBUG: User {user.id} is {status_str}. Skipping Force Join.", flush=True)
            return True
        print(f"DEBUG: User is {status_str}, checking force join rules...", flush=True)
    except Exception as e:
        print(f"DEBUG: Admin check failed: {e} - Proceeding with force join check", flush=True)

    # -------- STATS --------
    try:
        await inc_message()
    except Exception:
        pass

    try:
        await group_stats.update_one(
            {"group_id": chat.id},
            {"$inc": {"messages": 1}},
            upsert=True
        )
    except Exception:
        pass

    try:
        await users.update_one(
            {"user_id": user.id},
            {"$set": {"user_id": user.id}},
            upsert=True
        )
    except Exception:
        pass

    # -------- SETTINGS --------
    settings = await group_settings.find_one({"group_id": chat.id})
    if not settings:
        print(f"DEBUG: No settings found for group {chat.id} (Force Join DB empty/missing)", flush=True)
        return True

    channels = settings.get("channels", [])
    channels = settings.get("channels", [])
    if not channels:
        print("DEBUG: Group has settings but NO channels added.", flush=True)
        return True

    print(f"DEBUG: Checking against channels: {channels}", flush=True)

    # -------- CHECK JOIN --------
    not_joined = []

    for ch in channels:
        ch_username = ch["username"]
        print(f"DEBUG: Checking if user {user.id} is in channel {ch_username}", flush=True)
        try:
            await client.get_chat_member(ch_username, user.id)
            print(f"DEBUG: ✅ User IS in {ch_username}", flush=True)
        except UserNotParticipant:
            print(f"DEBUG: ❌ User NOT in {ch_username}", flush=True)
            not_joined.append(ch)
        except Exception as err:
            print(f"DEBUG: ⚠️ Error checking {ch_username}: {err}", flush=True)
            not_joined.append(ch)

    # -------- USER JOINED ALL --------
    if not not_joined:
        print(f"DEBUG: ✅ User {user.id} has joined ALL channels. Allowing message.", flush=True)
        key = (chat.id, user.id)
        WARN_COUNT.pop(key, None)

        old = FORCE_WARNINGS.pop(key, None)
        if old:
            try:
                await client.delete_messages(chat.id, old)
            except Exception:
                pass
        return True

    # -------- ENFORCE --------
    print("DEBUG: User has NOT joined all channels. Enforcing...", flush=True)
    try:
        await message.delete()
        print(f"DEBUG: Deleted message {message.id} from {user.id}", flush=True)
    except Exception as e:
        print(f"DEBUG: FAILED to delete message {message.id}: {e}", flush=True)

    key = (chat.id, user.id)
    WARN_COUNT[key] += 1
    
    print(f"DEBUG: Warning count for user {user.id}: {WARN_COUNT[key]}/{MAX_WARNINGS}", flush=True)

    try:
        await inc_force_action()
        await group_stats.update_one(
            {"group_id": chat.id},
            {"$inc": {"actions": 1}},
            upsert=True
        )
    except Exception:
        pass

    # -------- MUTE AFTER LIMIT --------
    if WARN_COUNT[key] >= MAX_WARNINGS:
        print(f"DEBUG: 🚨 MAX WARNINGS REACHED! Attempting to mute user {user.id} for 5 hours...", flush=True)
        try:
            await client.restrict_chat_member(
                chat.id,
                user.id,
                ChatPermissions(can_send_messages=False),
                until_date=datetime.now() + timedelta(hours=5)
            )
            print(f"DEBUG: ✅ Successfully muted user {user.id}", flush=True)
        except Exception as e:
            print(f"DEBUG: ❌ FAILED to mute user {user.id}: {e}", flush=True)

        # Cleanup previous warning
        old = FORCE_WARNINGS.pop(key, None)
        if old:
            try:
                await client.delete_messages(chat.id, old)
            except Exception:
                pass

        # Send Mute Message -> Wait 12s -> Delete
        try:
            mute_msg = await client.send_message(
                chat.id,
                f"🚫 {user.mention} **Muted for 5 hours**\nToo many warnings ignored.",
            )
            # Reset count so they can try again after unmute? 
            # Or keep them muted? Logic says "automute". 
            # If we reset count immediately they might get warned again if they are unmuted early.
            # safe to reset count.
            WARN_COUNT.pop(key, None) 
            
            await asyncio.sleep(12)
            await mute_msg.delete()
        except Exception:
            pass
            
        return False

    # -------- BUTTONS --------
    buttons = []

    for ch in not_joined:
        invite = ch.get("invite")
        url = invite if valid_url(invite) else f"https://t.me/{ch['username']}"
        if valid_url(url):
            buttons.append(
                [InlineKeyboardButton(f"Join @{ch['username']}", url=url)]
            )

    buttons.append(
        [InlineKeyboardButton("✅ I Joined", callback_data=f"recheck:{chat.id}")]
    )

    text = (
        f"🚫 **Force Join Required**\n\n"
        f"👤 {user.mention}\n"
        f"⚠️ Warning: {WARN_COUNT[key]}/{MAX_WARNINGS}\n\n"
        f"➡️ Channels join karo, phir **I Joined** dabao."
    )

    old = FORCE_WARNINGS.get(key)
    if old:
        try:
            await client.delete_messages(chat.id, old)
        except Exception:
            pass

    warn = await client.send_message(
        chat.id,
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    FORCE_WARNINGS[key] = warn.id
    
    # Auto-delete warning message after 12 seconds
    asyncio.create_task(auto_delete_warning(client, chat.id, warn.id, 12))

    return False


async def auto_delete_warning(client, chat_id, message_id, delay):
    """Delete a warning message after a delay"""
    try:
        await asyncio.sleep(delay)
        await client.delete_messages(chat_id, message_id)
    except Exception:
        pass
