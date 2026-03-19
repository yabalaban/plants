import os
from fastapi import APIRouter, Depends
import aiosqlite
from app.database import get_db
from app.services.scheduler import job_fetch_weather, job_send_reminders

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/weather")
async def get_weather_cache(db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute(
        "SELECT date, temp_high, temp_low, humidity, precipitation_mm, fetched_at "
        "FROM weather_cache ORDER BY date DESC LIMIT 30"
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


@router.post("/weather/fetch")
async def trigger_weather_fetch():
    await job_fetch_weather()
    return {"status": "ok"}


@router.post("/reminders/send")
async def trigger_reminders():
    await job_send_reminders()
    return {"status": "ok"}


@router.post("/reminders/preview")
async def preview_reminder():
    from app.services.telegram import format_watering_reminder, send_message
    from app.settings import load_settings
    fake_plants = [
        {"name": "Big Money", "status": "overdue"},
        {"name": "Small Money", "status": "due"},
    ]
    message = format_watering_reminder(fake_plants)
    settings = load_settings()
    if not message or not settings.telegram.bot_token:
        return {"status": "no_config"}
    await send_message(settings.telegram.bot_token, settings.telegram.chat_id, message, parse_mode="MarkdownV2")
    return {"status": "sent"}


@router.post("/health-check-all")
async def trigger_health_check_all(db: aiosqlite.Connection = Depends(get_db)):
    import json as _json
    from app.services.claude import check_plant_health
    cursor = await db.execute("SELECT id, species, photo_path, health_status FROM plants WHERE species IS NOT NULL")
    plants = [dict(row) for row in await cursor.fetchall()]
    checked = 0
    for p in plants:
        if p["health_status"]:
            continue
        # Translate web path to filesystem path
        photo_dir = os.environ.get("PLANTS_PHOTO_DIR", "./photos")
        photo_path = str(p["photo_path"])
        species: str | None = str(p["species"]) if p["species"] else None
        photo_file = os.path.join(photo_dir, os.path.basename(photo_path))
        health = await check_plant_health(photo_file, species)
        if health:
            await db.execute("UPDATE plants SET health_status = ? WHERE id = ?", (_json.dumps(health), p["id"]))
            await db.commit()
            checked += 1
    return {"status": "ok", "checked": checked, "skipped": len(plants) - checked}


@router.get("/claude-logs")
async def get_claude_logs(db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute(
        "SELECT id, task, prompt, response, error, duration_ms, created_at "
        "FROM claude_logs ORDER BY created_at DESC LIMIT 50"
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
