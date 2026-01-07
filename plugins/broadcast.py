import asyncio
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from config import OWNER_ID, BROADCAST_DELAY
from database import users

BROADCAST_RUNNING = False

async def broadcast(client, message):
    global BROADCAST_RUNNING

    from plugins.aauth import is_authorized
    if not await is_authorized(message.from_user.id):
        return await message.reply("❌ Only owner and authorized users can broadcast.")

    if not message.reply_to_message:
        return await message.reply("Reply to a message to broadcast.")

    BROADCAST_RUNNING = True
    msg = await message.reply("📢 Broadcasting...")

    try:
        total = await users.count_documents({})
    except Exception:
        total = 0

    sent = 0

    cancel_btn = InlineKeyboardMarkup(
        [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
    )

    await msg.edit("📢 Broadcasting started...", reply_markup=cancel_btn)

    async for u in users.find({}):
        if not BROADCAST_RUNNING:
            return await msg.edit("❌ Broadcast Cancelled")

        try:
            await message.reply_to_message.copy(u["user_id"])
            sent += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            pass

        if total and sent % 25 == 0:
            pct = int((sent / total) * 100)
            await msg.edit(
                f"📢 Progress: {pct}%  ({sent}/{total})",
                reply_markup=cancel_btn
            )

        await asyncio.sleep(BROADCAST_DELAY)

    await msg.edit(f"✅ Broadcast Done\nSent: {sent}/{total}")

async def cancel_broadcast(client, callback):
    global BROADCAST_RUNNING
    BROADCAST_RUNNING = False
    await callback.answer("Broadcast cancelled", show_alert=True)
