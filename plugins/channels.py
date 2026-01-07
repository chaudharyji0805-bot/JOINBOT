import re
from database import group_settings
from plugins.notify import notify_force_set, notify_channel_remove


def _clean_username(s: str) -> str:
    s = s.strip()
    s = s.replace("https://t.me/", "").replace("http://t.me/", "")
    if s.startswith("@"):
        s = s[1:]
    return s


def _is_valid_invite(url: str) -> bool:
    if not url:
        return False
    return bool(
        re.match(r"^https://t\.me/(joinchat/|\+)[A-Za-z0-9_-]+$", url)
    ) or url.startswith("https://t.me/")


async def add_channel(client, message):
    print("DEBUG: Entered add_channel function")
    if not message.from_user:
        return

    # admin check
    is_admin = False
    try:
        member = await client.get_chat_member(
            message.chat.id, message.from_user.id
        )
        status = str(member.status).lower().replace("chatmemberstatus.", "")
        if status in ("owner", "creator"):
            is_admin = True
        elif status == "administrator":
            # Check for "Add Admins" right
            if member.privileges and member.privileges.can_promote_members:
                is_admin = True
    except Exception:
        pass

    # Check database approval
    if not is_admin:
        doc = await group_settings.find_one({"group_id": message.chat.id})
        if doc and message.from_user.id in doc.get("admins", []):
            is_admin = True

    if not is_admin:
        return await message.reply(
            "❌ **Permission Denied**\n\n"
            "You need **Add Admin** rights to use this.\n"
            "💡 Or ask the **Group Owner** to reply to you with `/adminapprove`."
        )

    # Parse args manually to ensure newlines are handled
    # message.command is usually good but splitting text is explicit for newlines
    if message.text:
        parts = message.text.split()
        # [0] is command, [1:] are args
        args = parts[1:]
    else:
        args = []

    if not args:
        return await message.reply(
            "Usage:\n"
            "• `/fchannel @channel`\n"
            "• `/fchannel @ch1 @ch2 @ch3`\n"
            "• `/fchannel @channel https://t.me/+invite`"
        )

    # -------- DETECT MODE --------
    # Check if specifically: /addchannel @channel LINK
    # We must be careful about "is_single_with_link"
    # If len is 2 and 2nd is link -> Single
    is_single_with_link = False
    if len(args) == 2 and _is_valid_invite(args[1]):
        is_single_with_link = True

    channels_to_add = []

    if is_single_with_link:
        # SINGLE + LINK
        username = _clean_username(args[0])
        invite = args[1]
        channels_to_add.append({"username": username, "invite": invite})
    else:
        # BATCH (Usernames only)
        for arg in args:
            u = _clean_username(arg)
            if "/" not in u and u:
                channels_to_add.append({"username": u})


    if not channels_to_add:
        return await message.reply("❌ No valid channels found.")

    # -------- SAVE --------
    doc = await group_settings.find_one(
        {"group_id": message.chat.id}
    ) or {"group_id": message.chat.id, "channels": []}

    existing_channels = doc.get("channels", [])
    added_names = []

    for new_ch in channels_to_add:
        # Check duplicate
        if any(c.get("username") == new_ch["username"] for c in existing_channels):
            continue
        
        existing_channels.append(new_ch)
        added_names.append(f"@{new_ch['username']}")

    if not added_names:
        return await message.reply("ℹ️ All channels were already added.")

    await group_settings.update_one(
        {"group_id": message.chat.id},
        {"$set": {"channels": existing_channels}},
        upsert=True
    )

    # Notify & Reply
    joined_names = ", ".join(added_names)
    await notify_force_set(client, message.chat, joined_names)
    await message.reply(f"✅ Added {len(added_names)} channels:\n{joined_names}")


async def remove_channel(client, message):
    if not message.from_user:
        return

    # admin check
    is_admin = False
    try:
        member = await client.get_chat_member(
            message.chat.id, message.from_user.id
        )
        status = str(member.status).lower().replace("chatmemberstatus.", "")
        if status in ("owner", "creator"):
            is_admin = True
        elif status == "administrator":
            # Check for "Add Admins" right
            if member.privileges and member.privileges.can_promote_members:
                is_admin = True
    except Exception:
        pass

    # Check database approval
    if not is_admin:
        doc = await group_settings.find_one({"group_id": message.chat.id})
        if doc and message.from_user.id in doc.get("admins", []):
            is_admin = True

    if not is_admin:
        return await message.reply(
            "❌ **Permission Denied**\n\n"
            "You need **Add Admin** rights to use this.\n"
            "💡 Or ask the **Group Owner** to reply to you with `/adminapprove`."
        )

    if len(message.command) < 2:
        return await message.reply("Usage:\n/removechannel @channel")

    username = _clean_username(message.command[1])

    doc = await group_settings.find_one(
        {"group_id": message.chat.id}
    ) or {}

    channels = doc.get("channels", [])
    new_channels = [c for c in channels if c.get("username") != username]

    await group_settings.update_one(
        {"group_id": message.chat.id},
        {"$set": {"channels": new_channels}},
        upsert=True
    )

    await notify_channel_remove(client, message.chat, username)
    await message.reply(f"✅ Removed: @{username}")
