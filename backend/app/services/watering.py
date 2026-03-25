from datetime import datetime, timedelta
import aiosqlite


def compute_next_watering(interval_days: float, from_time: datetime | None = None) -> datetime:
    base = from_time or datetime.now()
    return base + timedelta(days=interval_days)


async def get_plants_needing_water(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute("""
        SELECT p.id, p.name, s.next_watering, s.interval_days
        FROM plants p JOIN watering_schedules s ON p.id = s.plant_id
        WHERE date(s.next_watering) <= date('now')
        ORDER BY s.next_watering ASC
    """)
    rows = await cursor.fetchall()
    result = []
    for row in rows:
        next_dt = datetime.fromisoformat(row["next_watering"])
        now = datetime.now()
        status = "overdue" if next_dt.date() < now.date() else "due"
        result.append({"id": row["id"], "name": row["name"], "next_watering": row["next_watering"],
                       "interval_days": row["interval_days"], "status": status})
    return result
