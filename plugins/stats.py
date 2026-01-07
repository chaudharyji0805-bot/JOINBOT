from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import users, channels, premium, group_settings, aauth_users
from plugins.aauth import is_authorized


async def global_stats_command(client, message):
    if not await is_authorized(message.from_user.id):
        return
        
    status_msg = await message.reply("⏳ Fetching stats...")
    
    try:
        total_users = await users.count_documents({})
    except:
        total_users = 0

    try:
        total_groups = await group_settings.count_documents({})
    except:
        total_groups = 0
        
    # Active groups? "how many are using actively"
    # We can check group_stats for groups with > 0 messages or actions?
    # Or just return total groups added. 
    # Let's count groups with at least 1 message recorded in group_stats as "Active"?
    # Or just total groups is enough for now.
    
    text = (
        "📊 **Global Bot Stats**\n\n"
        f"👤 Total Users: {total_users}\n"
        f"🛡️ Total Groups: {total_groups}\n"
        f"👮 Authorized Users: {await aauth_users.count_documents({})}"
    )
    
    await status_msg.edit(text)


async def inline_stats(client, callback):
    try:
        total_users = await users.count_documents({})
    except Exception:
        total_users = 0

    try:
        total_premium = await premium.count_documents({})
    except Exception:
        total_premium = 0

    try:
        total_channels = await channels.count_documents({})
    except Exception:
        total_channels = 0
    
    try:
        total_groups = await group_settings.count_documents({})
    except:
        total_groups = 0

    text = (
        "📊 **Bot Statistics**\n\n"
        f"👤 Users: {total_users}\n"
        f"🛡️ Groups: {total_groups}\n"
        f"💎 Premium: {total_premium}\n"
        f"📣 Channels: {total_channels}"
    )

    try:
        await callback.message.edit(
            text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="panel")]]
            )
        )
    except Exception:
        pass
