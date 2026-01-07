from database import group_settings


async def cleanup_groups(client):
    try:
        dialogs = [
            d.chat.id
            async for d in client.get_dialogs()
            if d.chat and d.chat.type in ("group", "supergroup")
        ]
    except Exception:
        dialogs = []

    async for g in group_settings.find({}):
        gid = g.get("group_id")
        if not gid:
            continue

        if gid not in dialogs:
            try:
                await group_settings.delete_one({"group_id": gid})
            except Exception:
                pass
