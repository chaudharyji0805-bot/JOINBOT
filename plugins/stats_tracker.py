import time
from database import stats

BOT_START_TIME = int(time.time())


async def init_stats():
    try:
        doc = await stats.find_one({"_id": "global"})
        if not doc:
            await stats.insert_one({
                "_id": "global",
                "messages_checked": 0,
                "force_actions": 0
            })
    except Exception:
        pass


async def inc_message():
    # fire-and-forget (safe)
    try:
        await stats.update_one(
            {"_id": "global"},
            {"$inc": {"messages_checked": 1}},
            upsert=True
        )
    except Exception:
        pass


async def inc_force_action():
    try:
        await stats.update_one(
            {"_id": "global"},
            {"$inc": {"force_actions": 1}},
            upsert=True
        )
    except Exception:
        pass


def get_uptime():
    seconds = int(time.time()) - BOT_START_TIME
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"
