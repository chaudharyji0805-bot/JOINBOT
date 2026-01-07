from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message
import asyncio
from database import group_settings
from plugins.aauth import is_authorized

@Client.on_message(filters.command("gban"))
async def gban_handler(client: Client, message: Message):
    if not message.from_user:
        return

    # Auth check
    if not await is_authorized(message.from_user.id):
        # Silent ignore or reply? Typically silence for unauthorized to avoid spam, 
        # but user asked for restrictions, so let's ignore.
        return

    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply("Usage: /gban [username/id/reply] [reason (optional)]")

    # Resolve target
    target_user = None
    reason = None
    
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        if len(message.command) > 1:
            reason = " ".join(message.command[1:])
    else:
        try:
            target_input = message.command[1]
            if target_input.isdigit():
                 target_user = await client.get_users(int(target_input))
            else:
                 target_user = await client.get_users(target_input)
            
            if len(message.command) > 2:
                reason = " ".join(message.command[2:])
        except Exception as e:
            return await message.reply(f"❌ Invalid user: {e}")

    if not target_user:
        return await message.reply("❌ Could not resolve user.")

    status_msg = await message.reply(f"⏳ Global banning {target_user.mention}...")

    # Get all groups
    # We use group_settings as a proxy for known groups.
    # Alternatively we could iterate dialogs but that's slow and API heavy.
    # We will use group_settings because existing code suggests we track groups there.
    all_groups_cursor = group_settings.find({})
    
    banned_count = 0
    failed_count = 0
    
    async for doc in all_groups_cursor:
        chat_id = doc.get("group_id")
        if not chat_id:
            continue
            
        try:
            await client.ban_chat_member(chat_id, target_user.id)
            banned_count += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                await client.ban_chat_member(chat_id, target_user.id)
                banned_count += 1
            except:
                failed_count += 1
        except Exception:
            failed_count += 1

    await status_msg.edit(
        f"✅ **GBan Complete**\n\n"
        f"👤 User: {target_user.mention}\n"
        f"🆔 ID: `{target_user.id}`\n"
        f"🔨 Banned in: {banned_count} groups\n"
        f"⚠️ Failed in: {failed_count} groups\n"
        f"📝 Reason: {reason or 'No reason provided'}"
    )
