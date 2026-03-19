from fastapi import APIRouter, Depends
import aiosqlite
from app.database import get_db
from app.services.scheduler import job_fetch_weather

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


@router.get("/claude-logs")
async def get_claude_logs(db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute(
        "SELECT id, task, prompt, response, error, duration_ms, created_at "
        "FROM claude_logs ORDER BY created_at DESC LIMIT 50"
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
