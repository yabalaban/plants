import logging
from datetime import datetime
import aiosqlite
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import get_db_path
from app.services.claude import adjust_schedules
from app.services.telegram import format_watering_reminder, send_message
from app.services.watering import get_plants_needing_water
from app.services.weather import fetch_weather
from app.settings import load_settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def job_fetch_weather():
    settings = load_settings()
    if not settings.location.latitude:
        logger.warning("No location configured, skipping weather fetch")
        return
    try:
        days = await fetch_weather(settings.location.latitude, settings.location.longitude, days=1)
    except Exception:
        logger.exception("Weather fetch failed")
        return
    async with aiosqlite.connect(get_db_path()) as db:
        for day in days:
            await db.execute("INSERT OR REPLACE INTO weather_cache (date, temp_high, temp_low, humidity, precipitation_mm) VALUES (?, ?, ?, ?, ?)",
                (day["date"], day["temp_high"], day["temp_low"], day["humidity"], day["precipitation_mm"]))
        await db.commit()


async def job_send_reminders():
    settings = load_settings()
    if not settings.telegram.bot_token:
        return
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        due_plants = await get_plants_needing_water(db)
    message = format_watering_reminder(due_plants)
    if message:
        await send_message(settings.telegram.bot_token, settings.telegram.chat_id, message)


async def job_adjust_schedules():
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute("SELECT p.id, p.species, s.interval_days FROM plants p JOIN watering_schedules s ON p.id = s.plant_id WHERE p.species IS NOT NULL")
        plants = [dict(row) for row in await cursor.fetchall()]
        if not plants:
            return
        cursor = await db.execute("SELECT date, temp_high, temp_low, humidity, precipitation_mm FROM weather_cache WHERE date >= date('now', '-7 days') ORDER BY date")
        weather = [dict(row) for row in await cursor.fetchall()]
        if not weather:
            return
    adjustments = await adjust_schedules(plants, weather)
    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        for adj in adjustments:
            await db.execute("""
                UPDATE watering_schedules SET interval_days = ?, last_adjusted = CURRENT_TIMESTAMP,
                    adjustment_reason = ?, next_watering = datetime(
                        (SELECT watered_at FROM watering_logs WHERE plant_id = ? ORDER BY watered_at DESC LIMIT 1),
                        '+' || ? || ' days')
                WHERE plant_id = ?
            """, (adj["interval_days"], adj.get("reason", "weather adjustment"), adj["plant_id"], int(adj["interval_days"]), adj["plant_id"]))
        await db.commit()


def start_scheduler():
    scheduler.add_job(job_fetch_weather, CronTrigger(hour=6, minute=0), id="fetch_weather", replace_existing=True)
    settings = load_settings()
    hour, minute = (int(x) for x in settings.reminder_time.split(":"))
    scheduler.add_job(job_send_reminders, CronTrigger(hour=hour, minute=minute), id="send_reminders", replace_existing=True)
    scheduler.add_job(job_adjust_schedules, CronTrigger(day_of_week="mon", hour=7, minute=0), id="adjust_schedules", replace_existing=True)
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown(wait=False)
