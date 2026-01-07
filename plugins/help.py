from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

HELP_TEXT_PRIVATE = """
🤖 **Force Join Bot – Help**

👤 **User**
/start – Bot start
/help – Help message

👮 **Admins (Group)**
/addchannel @channel [invite_link]
/removechannel @channel
/listchannels
/stats
"""

HELP_TEXT_GROUP = """
🤖 **Force Join Bot – Help (Group)**

• Required channels join karo
• "✅ I Joined" button se recheck

👮 **Admins**
/addchannel @channel [invite_link]
/removechannel @channel
/listchannels
/stats
"""

def start_buttons():
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("📖 Help", callback_data="help"),
            InlineKeyboardButton("ℹ️ About", callback_data="about")
        ]]
    )

def close_button():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("❌ Close", callback_data="close")]]
    )

async def help_command(client, message):
    if message.chat.type == "private":
        await message.reply(
            HELP_TEXT_PRIVATE,
            reply_markup=close_button(),
            disable_web_page_preview=True,
        )
    else:
        await message.reply(
            HELP_TEXT_GROUP,
            reply_markup=close_button(),
            disable_web_page_preview=True,
        )
