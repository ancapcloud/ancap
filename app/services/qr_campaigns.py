"""Anonymous aggregate counters with an atomic PostgreSQL upsert."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from app.db.models import QrDailyCount
from app.schemas.qr_campaigns import QrStats, QrDay

CAMPAIGN = "street"
DESTINATION = "https://ancap.cloud/?utm_source=qr&utm_medium=sticker&utm_campaign=street"

def campaign_day():
    return datetime.now(ZoneInfo("Europe/Berlin")).date()

def should_count(method, headers):
    # HEAD, speculative loads and obvious crawlers do not count. This is not
    # bot-proof and does not claim to count distinct humans.
    purpose = " ".join(headers.get(k, "") for k in ("purpose", "sec-purpose", "x-purpose")).lower()
    ua = headers.get("user-agent", "").lower()
    return method == "GET" and not any(x in purpose for x in ("prefetch", "preview")) and not any(
        x in ua for x in ("bot", "crawler", "spider", "facebookexternalhit", "whatsapp", "telegram", "slack", "discord"))

async def record_visit(session):
    stmt = insert(QrDailyCount).values(campaign=CAMPAIGN, day=campaign_day(), visits=1)
    await session.execute(stmt.on_conflict_do_update(
        index_elements=[QrDailyCount.campaign, QrDailyCount.day],
        set_={"visits": QrDailyCount.visits + 1}))

async def get_stats(session, days):
    today = campaign_day()
    total = await session.scalar(select(func.coalesce(func.sum(QrDailyCount.visits), 0)).where(QrDailyCount.campaign == CAMPAIGN))
    rows = (await session.execute(select(QrDailyCount).where(
        QrDailyCount.campaign == CAMPAIGN,
        QrDailyCount.day >= today - timedelta(days=days-1),
        QrDailyCount.day <= today))).scalars().all()
    counts = {row.day: row.visits for row in rows}
    return QrStats(campaign=CAMPAIGN, total=int(total or 0), today=counts.get(today, 0), timezone="Europe/Berlin",
        days=[QrDay(day=today-timedelta(days=i), visits=counts.get(today-timedelta(days=i), 0)) for i in range(days-1, -1, -1)])
