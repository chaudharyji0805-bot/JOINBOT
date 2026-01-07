from pyrogram import Client, filters
from database import aauth_users
from config import OWNERS

async def is_authorized(user_id: int) -> bool:
    if user_id in OWNERS:
        return True
    return bool(await aauth_users.find_one({"user_id": user_id}))

@Client.on_message(filters.command("aauth") & filters.user(OWNERS))
async def aauth_handler(client, message):
    if not message.from_user:
        return

    target_user_id = None
    target_username = None

    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        target_username = message.reply_to_message.from_user.username
    elif len(message.command) > 1:
        try:
            target_user_id = int(message.command[1])
        except ValueError:
            target_user_id = message.command[1]
            
    if not target_user_id:
        return await message.reply("❌ **Usage:** Reply to a user or provide an ID/Username to authorize.")

    # If it's a string (username), try to resolve it to ID for stability
    if isinstance(target_user_id, str) and not str(target_user_id).isdigit():
        try:
            u = await client.get_users(target_user_id)
            target_user_id = u.id
            target_username = u.username
        except Exception as e:
            return await message.reply(f"❌ **Error:** Could not resolve user '{target_user_id}'.")
    else:
        # Ensure it's an int if digit
        target_user_id = int(target_user_id)
    
    # Add to DB
    await aauth_users.update_one(
        {"user_id": target_user_id},
        {"$set": {"user_id": target_user_id, "username": target_username or "Unknown"}},
        upsert=True
    )
    
    await message.reply(f"✅ **User Authorized**\n\nUser `{target_user_id}` (@{target_username or 'Unknown'}) can now use restricted commands and bypass force join.")

@Client.on_message(filters.command("unaauth") & filters.user(OWNERS))
async def unaauth_handler(client, message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply("❌ **Usage:** /unaauth [id/username/reply]")

    target_user_id = None
    
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
    else:
        try:
            target_user_id = int(message.command[1])
        except ValueError:
            try:
                u = await client.get_users(message.command[1])
                target_user_id = u.id
            except:
                return await message.reply("❌ **Error:** Invalid user.")

    result = await aauth_users.delete_one({"user_id": target_user_id})
    if result.deleted_count > 0:
        await message.reply(f"✅ **Authorization Removed**\n\nUser `{target_user_id}` is no longer authorized.")
    else:
        await message.reply("ℹ️ User was not in the authorized list.")
