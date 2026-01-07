from config import LOG_GROUP_ID
from pyrogram.enums import ParseMode


def safe(text: str) -> str:
    if not text:
        return ""
    for ch in ("_", "*", "`", "[", "]", "(", ")"):
        text = text.replace(ch, f"\\{ch}")
    return text


async def notify_bot_start(client):
    if not LOG_GROUP_ID:
        return
    try:
        await client.send_message(
            LOG_GROUP_ID,
            "🚀 **Bot Started Successfully**\n\n✅ Status: Online",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        pass


async def notify_group_add(client, chat):
    if not LOG_GROUP_ID or not chat:
        return
    try:
        title = safe(chat.title or "Unknown Group")
        await client.send_message(
            LOG_GROUP_ID,
            f"➕ **Bot Added to Group**\n\n"
            f"📛 Group: {title}\n"
            f"🆔 ID: `{chat.id}`",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        pass


async def notify_bot_admin(client, chat, user):
    if not LOG_GROUP_ID or not chat:
        return
    try:
        title = safe(chat.title or "Unknown Group")
        name = safe(user.first_name if user else "Unknown")
        await client.send_message(
            LOG_GROUP_ID,
            f"👮‍♂️ **Bot Promoted to Admin**\n\n"
            f"📛 Group: {title}\n"
            f"🆔 Group ID: `{chat.id}`\n"
            f"👤 By: {name}",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        pass


async def notify_user_start(client, user):
    if not LOG_GROUP_ID or not user:
        return
    try:
        name = safe(user.first_name or "Unknown")
        await client.send_message(
            LOG_GROUP_ID,
            f"👤 **User Started Bot (DM)**\n\n"
            f"👤 Name: {name}\n"
            f"🆔 ID: `{user.id}`",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        pass


async def notify_force_set(client, chat, channel):
    if not LOG_GROUP_ID or not chat:
        return
    try:
        title = safe(chat.title or "Unknown Group")
        channel = safe(str(channel))
        await client.send_message(
            LOG_GROUP_ID,
            f"⚙️ **Force Join Updated**\n\n"
            f"📛 Group: {title}\n"
            f"🆔 Group ID: `{chat.id}`\n"
            f"📢 Channel: `{channel}`",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        pass


async def notify_channel_remove(client, chat, channel):
    if not LOG_GROUP_ID or not chat:
        return
    try:
        title = safe(chat.title or "Unknown Group")
        channel = safe(str(channel))
        await client.send_message(
            LOG_GROUP_ID,
            f"🗑 **Force Join Removed**\n\n"
            f"📛 Group: {title}\n"
            f"🆔 Group ID: `{chat.id}`\n"
            f"📢 Channel: `{channel}`",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        pass

