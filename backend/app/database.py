import os
import aiosqlite

_DB_PATH_DEFAULT = "plants.db"


def get_db_path() -> str:
    return os.environ.get("PLANTS_DB_PATH", _DB_PATH_DEFAULT)


async def get_db():
    db = await aiosqlite.connect(get_db_path())
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
    finally:
        await db.close()


async def init_db():
    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                species TEXT,
                location TEXT NOT NULL DEFAULT 'indoor',
                photo_path TEXT NOT NULL,
                identification_details TEXT,
                base_watering_interval_days INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS watering_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id INTEGER NOT NULL
                    REFERENCES plants(id) ON DELETE CASCADE,
                watered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS watering_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id INTEGER NOT NULL UNIQUE
                    REFERENCES plants(id) ON DELETE CASCADE,
                interval_days REAL NOT NULL,
                next_watering TIMESTAMP NOT NULL,
                last_adjusted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                adjustment_reason TEXT
            );

            CREATE TABLE IF NOT EXISTS weather_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,
                temp_high REAL,
                temp_low REAL,
                humidity REAL,
                precipitation_mm REAL,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS claude_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                prompt TEXT NOT NULL,
                response TEXT,
                error TEXT,
                duration_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Migrations
        cursor = await db.execute("PRAGMA table_info(plants)")
        columns = {row[1] for row in await cursor.fetchall()}
        if "location" not in columns:
            await db.execute("ALTER TABLE plants ADD COLUMN location TEXT NOT NULL DEFAULT 'indoor'")
        if "health_status" not in columns:
            await db.execute("ALTER TABLE plants ADD COLUMN health_status TEXT")
        await db.commit()
