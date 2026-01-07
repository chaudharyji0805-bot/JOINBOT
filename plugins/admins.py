from database import group_settings


def is_group_admin(data, user_id):
    if not data:
        return False
    return user_id in data.get("admins", [])


async def add_admin(client, message):
    if not message.chat or not message.from_user:
        return

    # Check if command user is the OWNER of the group
    # Check if command user is the OWNER or SUPER ADMIN of the group
    try:
        mem = await client.get_chat_member(message.chat.id, message.from_user.id)
        status = str(mem.status).lower().replace("chatmemberstatus.", "")
        has_right = False
        
        if status in ("owner", "creator"):
            has_right = True
        elif status == "administrator":
            # Check for "Add Admins" right
            if mem.privileges and mem.privileges.can_promote_members:
                has_right = True

        if not has_right:
            return await message.reply(f"❌ You need **Add Admin** rights to use this.\nYour status: `{status}`")
    except Exception:
        return

    uid = None
    # 1. Check reply
    if message.reply_to_message and message.reply_to_message.from_user:
        uid = message.reply_to_message.from_user.id
    # 2. Check arg
    elif len(message.command) >= 2:
        try:
            uid = int(message.command[1])
        except ValueError:
            pass
    
    if not uid:
        return await message.reply("Usage: Reply to user with `/adminapprove` (Owner Only)")

    gid = message.chat.id

    try:
        await group_settings.update_one(
            {"group_id": gid},
            {"$addToSet": {"admins": uid}},
            upsert=True,
        )
    except Exception:
        return await message.reply("❌ Failed to add admin")

    await message.reply(f"✅ User `{uid}` Approved to manage bot settings.")


async def remove_admin(client, message):
    if not message.chat or not message.from_user:
        return

    # Check if command user is the OWNER of the group
    # Check if command user is the OWNER of the group
    try:
        mem = await client.get_chat_member(message.chat.id, message.from_user.id)
        status = str(mem.status).lower().replace("chatmemberstatus.", "")
        if status not in ("owner", "creator"):
            return await message.reply(f"❌ Only the Group Owner can use this command.\nYour status: `{status}`")
    except Exception:
        return

    if len(message.command) < 2:
        return await message.reply("Usage: /removeadmin <user_id>")

    try:
        uid = int(message.command[1])
    except ValueError:
        return await message.reply("❌ Invalid user ID")

    gid = message.chat.id

    try:
        await group_settings.update_one(
            {"group_id": gid},
            {"$pull": {"admins": uid}},
        )
    except Exception:
        return await message.reply("❌ Failed to remove admin")

    await message.reply(f"❌ `{uid}` removed from group admin list")
