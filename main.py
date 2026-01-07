import asyncio
from pyrogram import Client, filters

from config import API_ID, API_HASH, BOT_TOKEN
from plugins.force_join import force_join_check
from plugins.start import start
from plugins.broadcast import broadcast, cancel_broadcast
from plugins.channels import add_channel, remove_channel
from plugins.listchannels import list_channels
from plugins.help import help_command, HELP_TEXT_PRIVATE, close_button
from plugins.stats import global_stats_command
from plugins.notify import (
    notify_group_add,
    notify_user_start,
    notify_force_set,
    notify_force_set,
    notify_bot_start,
    notify_bot_admin,
)
from plugins.stats_tracker import init_stats
from plugins.daily_report import daily_report
from plugins.group_stats import group_stats_cmd
from plugins.aauth import aauth_handler, unaauth_handler
from plugins.gban import gban_handler

# ---------------- APP ----------------

app = Client(
    "forcejoinbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# ---------------- HANDLERS ----------------

@app.on_message(filters.text, group=-1)
async def debug_logger(client, message):
   
    user = message.from_user.first_name if message.from_user else "Unknown"
print(f"🔍 RAW DEBUG: Msg '{message.text}' from {user} in {message.chat.type} ({message.chat.id})")


@app.on_message(filters.command("ping"))
async def ping_handler(client, message):
    await message.reply("PONG ✅")


@app.on_message(filters.command("help"))
async def help_handler(client, message):
    await help_command(client, message)


@app.on_message(filters.group & filters.command("gstats"))
async def stats_handler(client, message):
    await group_stats_cmd(client, message)


@app.on_message(filters.private & filters.command("stats"))
async def global_stats_handler(client, message):
    await global_stats_command(client, message)


# Logic moved to bottom to prevent blocking commands


@app.on_message(filters.private & filters.command("start"))
async def start_handler(client, message):
    await notify_user_start(client, message.from_user)
    await start(client, message)


@app.on_message(filters.private & filters.command("fchannel"))
async def add_channel_private_error(client, message):
    await message.reply("⚠️ **Wrong Chat!**\n\nYou must run this command **inside the Group** you want to configure.\n\n1. Add me to the Group.\n2. Type `/fchannel @channel` IN THE GROUP.")

@app.on_message(filters.group & filters.command("fchannel"))
async def add_channel_handler(client, message):
    print(f"DEBUG: /fchannel command received from {message.from_user.id}")
    await add_channel(client, message)


@app.on_message(filters.group & filters.command("removechannel"))
async def remove_channel_handler(client, message):
    await remove_channel(client, message)


@app.on_message(filters.group & filters.command("listchannels"))
async def list_channels_handler(client, message):
    await list_channels(client, message)


@app.on_message(filters.new_chat_members)
async def bot_added_handler(client, message):
    for m in message.new_chat_members:
        if m.is_self:
            await notify_group_add(client, message.chat)


@app.on_chat_member_updated(filters.group)
async def admin_check_handler(client, message):
    # Check if this update is about the bot
    if not message.new_chat_member:
        return
    
    if message.new_chat_member.user.is_self:
        # Check if promoted to admin
        was_admin = message.old_chat_member and message.old_chat_member.status in ("administrator", "owner")
        is_admin = message.new_chat_member.status in ("administrator", "owner")
        
        if is_admin and not was_admin:
            await notify_bot_admin(client, message.chat, message.from_user)



@app.on_callback_query(filters.regex("^recheck:"))
async def recheck_handler(client, callback):
    await callback.answer("🔍 Checking...")
    await force_join_check(client, callback.message, callback.from_user)


@app.on_callback_query(filters.regex("^help$"))
async def help_callback(client, callback):
    await callback.answer()
    await callback.message.edit_text(
        HELP_TEXT_PRIVATE,
        reply_markup=close_button(),
    )


@app.on_callback_query(filters.regex("^about$"))
async def about_callback(client, callback):
    await callback.answer()
    await callback.message.edit_text(
        "ℹ️ **About Bot**\n\nAdvanced Force Join Bot",
        reply_markup=close_button(),
    )


@app.on_callback_query(filters.regex("^close$"))
async def close_callback(client, callback):
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass


@app.on_message(filters.command("broadcast"))
async def broadcast_handler(client, message):
    await broadcast(client, message)


@app.on_message(filters.command("aauth"))
async def aauth_cmd_handler(client, message):
    await aauth_handler(client, message)


@app.on_message(filters.command("unaauth"))
async def unaauth_cmd_handler(client, message):
    await unaauth_handler(client, message)


@app.on_message(filters.command("gban"))
async def gban_cmd_handler(client, message):
    await gban_handler(client, message)


@app.on_callback_query(filters.regex("^cancel$"))
async def cancel_handler(client, callback):
    await cancel_broadcast(client, callback)


@app.on_callback_query(filters.regex("^bc$"))
async def bc_help_handler(client, callback):
    await callback.answer()
    await callback.message.edit(
        "📢 **How to Broadcast:**\n\n"
        "1. Write your message (or forward it).\n"
        "2. **Reply** to that message with `/broadcast`.\n\n"
        "The bot will copy that message to all users.",
        reply_markup=close_button()
    )



# -----------------------------------------------
# Catch-all Force Join (Must be last to not block commands)
@app.on_message(filters.group & ~filters.bot)
async def group_force_join(client, message):
    # If it's a command that wasn't handled above, ignore it? 
    # Or just let force join check run.
    # But if we are here, it means no previous handler matched? 
    # Wait, Pyrogram handlers order matters.
    # If a command matched above, it would have stopped.
    # So here we just run force join check on everything else.
    if message.text and message.text.startswith("/"):
        return
    await force_join_check(client, message)

# ---------------- BACKGROUND TASKS ----------------

async def background_tasks():
    try:
        await init_stats()
    except Exception as e:
        print("Stats init error:", e)

    try:
        await notify_bot_start(app)
    except Exception:
        pass

    try:
        asyncio.create_task(daily_report(app))
    except Exception as e:
        print("Daily report error:", e)


from plugins.admins import add_admin

@app.on_message(filters.group & filters.command("adminapprove"))
async def admin_approve_handler(client, message):
    await add_admin(client, message)

# ---------------- RUN ----------------

print("🚀 Starting bot...")

loop = asyncio.get_event_loop()
loop.create_task(background_tasks())

app.run()
