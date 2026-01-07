import asyncio
from database import users


async def scheduled_broadcast(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /schedule 10 (minutes)")

    if not message.reply_to_message:
        return await message.reply("Reply to a message to schedule broadcast.")

    try:
        minutes = int(message.command[1])
        if minutes <= 0:
            raise ValueError
    except ValueError:
        return await message.reply("❌ Invalid time. Example: /schedule 10")

    delay = minutes * 60
    reply = message.reply_to_message

    await message.reply("⏳ Broadcast scheduled")

    # wait before sending
    await asyncio.sleep(delay)

    async for u in users.find({}):
        try:
            await reply.copy(u.get("user_id"))
        except Exception:
            pass
