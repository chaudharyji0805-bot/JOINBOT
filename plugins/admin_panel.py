from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def admin_panel(client, message):
    try:
        await message.reply(
            "⚙️ **Admin Control Panel**",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("📊 Stats", callback_data="stats")],
                    [InlineKeyboardButton("📢 Broadcast", callback_data="bc")],
                    [InlineKeyboardButton("❌ Cancel Broadcast", callback_data="cancel")],
                ]
            ),
        )
    except Exception:
        # safety: never crash handler
        pass
