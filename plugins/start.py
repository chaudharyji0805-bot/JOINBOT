from database import users
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


SUPPORT_CHAT_LINK = "https://t.me/Yaaro_kimehfill"
SUPPORT_CHANNEL_LINK = "https://t.me/BotzEmpire"


def safe(text: str) -> str:
    if not text:
        return ""
    for ch in ("_", "*", "`", "[", "]", "(", ")"):
        text = text.replace(ch, f"\\{ch}")
    return text


def start_buttons(bot_username: str):
    bot_username = bot_username or ""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📖 Help", callback_data="help"),
                InlineKeyboardButton("ℹ️ About", callback_data="about"),
            ],
            [
                InlineKeyboardButton(
                    "➕ Add me to Group",
                    url=f"https://t.me/{bot_username}?startgroup=true"
                    if bot_username else "https://t.me"
                )
            ],
            [
                InlineKeyboardButton("💬 Support Chat", url=SUPPORT_CHAT_LINK),
                InlineKeyboardButton("📢 Support Channel", url=SUPPORT_CHANNEL_LINK),
            ],
            [
                InlineKeyboardButton("❌ Close", callback_data="close")
            ]
        ]
    )


async def start(client, message):
    user = message.from_user
    bot = await client.get_me()

    # save user in database
    if user:
        try:
            await users.update_one(
                {"user_id": user.id},
                {"$set": {"user_id": user.id}},
                upsert=True
            )
        except Exception:
            pass

    first_name = safe(user.first_name if user else "there")
    bot_name = safe(bot.first_name or "Force Join Bot")

    text = (
        f"👋 **Hey {first_name}!**\n\n"
        f"🤖 I am **{bot_name}** — an advanced **Force Join Bot**.\n\n"
        "✅ **Features:**\n"
        "• Per-group Force Join (multiple channels)\n"
        "• Auto delete message if not joined\n"
        "• 3 warnings → auto mute (1 hour)\n"
        "• Inline **✅ I Joined** recheck\n"
        "• Group stats `/stats`\n\n"
        "📌 **Setup (in group):**\n"
        "1) Add me to your group & make me **Admin**\n"
        "2) Add channels:\n"
        "   `/addchannel @channel`\n"
        "   `/addchannel @channel https://t.me/+invite`\n"
        "3) Check: `/listchannels`\n\n"
        "💡 **Tip:** Group Owners can reply to a user with `/adminapprove` to let them manage the bot without being Admin.\n\n"
        "👇 Use buttons below:"
    )

    await message.reply(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=start_buttons(bot.username)
    )
