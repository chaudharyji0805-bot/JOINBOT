from database import group_settings

async def list_channels(client, message):
    try:
        s = await group_settings.find_one({"group_id": message.chat.id}) or {}
    except Exception:
        s = {}

    channels = s.get("channels", [])

    if not channels:
        return await message.reply("ℹ️ No channels set for this group.")

    lines = []
    for i, ch in enumerate(channels, start=1):
        username = ch.get("username", "unknown")
        invite = ch.get("invite") or ""
        lines.append(f"{i}. @{username} {invite}".strip())

    await message.reply(
        "📌 **Channels for this group:**\n\n" + "\n".join(lines)
    )
