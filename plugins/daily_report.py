import asyncio
from datetime import datetime, timedelta, timezone

from config import LOG_GROUP_ID
from database import users, group_settings, stats
from plugins.stats_tracker import get_uptime

IST = timezone(timedelta(hours=5, minutes=30))


async def daily_report(client):
    if not LOG_GROUP_ID:
        return

    while True:
        try:
            now = datetime.now(IST)
            nxt = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            sleep_for = max(0, (nxt - now).total_seconds())
            await asyncio.sleep(sleep_for)

            try:
                s = await stats.find_one({"_id": "global"}) or {}
            except Exception:
                s = {}

            try:
                total_users = await users.count_documents({})
            except Exception:
                total_users = 0

            try:
                total_groups = await group_settings.count_documents({})
            except Exception:
                total_groups = 0

            text = (
                "📊 **Daily Bot Report**\n\n"
                f"⏱ Uptime: {get_uptime()}\n"
                f"👤 Total Users: {total_users}\n"
                f"👥 Active Groups: {total_groups}\n"
                f"💬 Messages Checked: {s.get('messages_checked', 0)}\n"
                f"📢 Force Actions: {s.get('force_actions', 0)}"
            )

            try:
                await client.send_message(LOG_GROUP_ID, text)
            except Exception:
                pass

        except Exception:
            # safety: loop never dies
            await asyncio.sleep(60)
