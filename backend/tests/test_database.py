import pytest
import aiosqlite
from app.database import init_db, get_db_path


@pytest.mark.asyncio
async def test_init_db_creates_tables(env_db_path):
    await init_db()
    async with aiosqlite.connect(env_db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in await cursor.fetchall()]
    assert "plants" in tables
    assert "watering_logs" in tables
    assert "watering_schedules" in tables
    assert "weather_cache" in tables


@pytest.mark.asyncio
async def test_foreign_keys_enabled(env_db_path):
    await init_db()
    async with aiosqlite.connect(env_db_path) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(
            "INSERT INTO plants (name, photo_path) VALUES (?, ?)",
            ("Test", "/tmp/test.jpg"),
        )
        await db.commit()
        await db.execute(
            "INSERT INTO watering_logs (plant_id, watered_at) VALUES (1, CURRENT_TIMESTAMP)"
        )
        await db.commit()
        await db.execute("DELETE FROM plants WHERE id = 1")
        await db.commit()
        cursor = await db.execute("SELECT COUNT(*) FROM watering_logs")
        count = (await cursor.fetchone())[0]
    assert count == 0


@pytest.mark.asyncio
async def test_init_db_idempotent(env_db_path):
    await init_db()
    await init_db()
    async with aiosqlite.connect(env_db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in await cursor.fetchall()]
    assert "plants" in tables
