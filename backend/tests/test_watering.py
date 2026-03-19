import pytest
from datetime import datetime, timedelta
from app.services.watering import get_plants_needing_water, compute_next_watering


def test_compute_next_watering():
    now = datetime(2026, 3, 18, 9, 0)
    result = compute_next_watering(interval_days=5, from_time=now)
    assert result == datetime(2026, 3, 23, 9, 0)


def test_compute_next_watering_fractional():
    now = datetime(2026, 3, 18, 9, 0)
    result = compute_next_watering(interval_days=3.5, from_time=now)
    expected = now + timedelta(days=3.5)
    assert result == expected


@pytest.mark.asyncio
async def test_get_plants_needing_water(env_db_path):
    import aiosqlite
    from app.database import init_db
    await init_db()
    async with aiosqlite.connect(env_db_path) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("INSERT INTO plants (name, photo_path) VALUES (?, ?)", ("Thirsty", "/tmp/t.jpg"))
        await db.execute("INSERT INTO watering_schedules (plant_id, interval_days, next_watering) VALUES (1, 5, datetime('now', '-1 day'))")
        await db.execute("INSERT INTO plants (name, photo_path) VALUES (?, ?)", ("Happy", "/tmp/h.jpg"))
        await db.execute("INSERT INTO watering_schedules (plant_id, interval_days, next_watering) VALUES (2, 7, datetime('now', '+3 days'))")
        await db.commit()
        due = await get_plants_needing_water(db)
    assert len(due) == 1
    assert due[0]["name"] == "Thirsty"
    assert due[0]["status"] == "overdue"
