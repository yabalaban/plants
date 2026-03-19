import asyncio
import json
import logging
import os
import shutil
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

import aiosqlite
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.database import get_db
from app.models import PlantDetailResponse, PlantResponse, PlantUpdate, WaterPlantRequest, WateringLogResponse
from app.services.claude import identify_plant, check_plant_health
from app.services.scheduler import job_adjust_schedules

router = APIRouter(prefix="/api/plants", tags=["plants"])


async def _identify_and_update(plant_id: int, photo_path: str):
    from app.database import get_db_path
    try:
        identification = await identify_plant(photo_path)
        if not identification:
            return

        # Validate LLM output
        interval = identification.get("base_watering_interval_days", 7)
        try:
            interval = int(interval)
        except (TypeError, ValueError):
            interval = 7
        if interval < 1 or interval > 90:
            interval = 7

        async with aiosqlite.connect(get_db_path()) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            # Check plant still exists (may have been deleted during identification)
            cursor = await db.execute("SELECT id FROM plants WHERE id = ?", (plant_id,))
            if not await cursor.fetchone():
                return
            await db.execute("""
                UPDATE plants SET species = ?, identification_details = ?, base_watering_interval_days = ?
                WHERE id = ?
            """, (identification.get("species"), json.dumps(identification), interval, plant_id))
            await db.execute("""
                INSERT OR REPLACE INTO watering_schedules (plant_id, interval_days, next_watering, adjustment_reason)
                VALUES (?, ?, datetime('now', '+' || ? || ' days'), 'initial schedule')
            """, (plant_id, interval, interval))
            await db.commit()
        # Health check on the same photo
        health = await check_plant_health(photo_path, identification.get("species"))
        if health:
            async with aiosqlite.connect(get_db_path()) as db:
                await db.execute(
                    "UPDATE plants SET health_status = ? WHERE id = ?",
                    (json.dumps(health), plant_id),
                )
                await db.commit()
        # Adjust schedule based on current weather data (if available)
        await job_adjust_schedules()
    except Exception:
        logger.exception("Background identification failed for plant %d", plant_id)


def _get_photo_dir() -> str:
    return os.environ.get("PLANTS_PHOTO_DIR", "./photos")


def _plant_from_row(row) -> PlantResponse:
    keys = row.keys() if hasattr(row, "keys") else []
    return PlantResponse(
        id=row["id"], name=row["name"], species=row["species"],
        location=row["location"], photo_path=row["photo_path"],
        identification_details=json.loads(row["identification_details"]) if row["identification_details"] else None,
        health_status=json.loads(row["health_status"]) if row["health_status"] else None,
        base_watering_interval_days=row["base_watering_interval_days"],
        created_at=row["created_at"],
        interval_days=row["interval_days"] if "interval_days" in keys else None,
        next_watering=row["next_watering"] if "next_watering" in keys else None,
        adjustment_reason=row["adjustment_reason"] if "adjustment_reason" in keys else None,
    )


@router.get("", response_model=list[PlantResponse])
async def list_plants(db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("""
        SELECT p.*, s.interval_days, s.next_watering, s.adjustment_reason
        FROM plants p
        LEFT JOIN watering_schedules s ON p.id = s.plant_id
        ORDER BY CASE WHEN s.next_watering IS NULL THEN 1 ELSE 0 END, s.next_watering ASC
    """)
    rows = await cursor.fetchall()
    return [_plant_from_row(row) for row in rows]


@router.post("", response_model=PlantResponse, status_code=201)
async def add_plant(
    name: str = Form(...),
    location: str = Form("indoor"),
    photo: UploadFile = File(...),
    db: aiosqlite.Connection = Depends(get_db),
):
    photo_dir = _get_photo_dir()
    os.makedirs(photo_dir, exist_ok=True)
    ext = os.path.splitext(photo.filename or "photo.jpg")[1].lower() or ".jpg"
    allowed_exts = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Unsupported image format: {ext}")
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(photo_dir, filename)

    with open(filepath, "wb") as f:
        content = await photo.read()
        f.write(content)

    web_path = f"/photos/{filename}"
    if location not in ("indoor", "balcony"):
        location = "indoor"
    cursor = await db.execute(
        "INSERT INTO plants (name, location, photo_path) VALUES (?, ?, ?)",
        (name, location, web_path),
    )
    await db.commit()
    plant_id = cursor.lastrowid

    cursor = await db.execute("SELECT * FROM plants WHERE id = ?", (plant_id,))
    row = await cursor.fetchone()
    asyncio.create_task(_identify_and_update(plant_id, filepath))
    return _plant_from_row(row)


@router.get("/{plant_id}", response_model=PlantDetailResponse)
async def get_plant(plant_id: int, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("""
        SELECT p.*, s.interval_days, s.next_watering, s.adjustment_reason
        FROM plants p
        LEFT JOIN watering_schedules s ON p.id = s.plant_id
        WHERE p.id = ?
    """, (plant_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Plant not found")

    cursor = await db.execute(
        "SELECT * FROM watering_logs WHERE plant_id = ? ORDER BY watered_at DESC",
        (plant_id,),
    )
    logs = await cursor.fetchall()
    base = _plant_from_row(row)
    return PlantDetailResponse(
        **base.model_dump(),
        watering_logs=[
            WateringLogResponse(id=log["id"], watered_at=log["watered_at"], notes=log["notes"])
            for log in logs
        ],
    )


@router.post("/{plant_id}/water", status_code=201)
async def water_plant(plant_id: int, body: WaterPlantRequest, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT id FROM plants WHERE id = ?", (plant_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Plant not found")

    await db.execute(
        "INSERT INTO watering_logs (plant_id, notes) VALUES (?, ?)",
        (plant_id, body.notes),
    )

    await db.execute("""
        UPDATE watering_schedules
        SET next_watering = datetime('now', '+' || interval_days || ' days')
        WHERE plant_id = ?
    """, (plant_id,))
    await db.commit()
    return {"status": "logged"}


@router.patch("/{plant_id}", response_model=PlantResponse)
async def update_plant(plant_id: int, body: PlantUpdate, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT id FROM plants WHERE id = ?", (plant_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Plant not found")
    if body.name is not None:
        await db.execute("UPDATE plants SET name = ? WHERE id = ?", (body.name, plant_id))
    if body.location is not None:
        if body.location not in ("indoor", "balcony"):
            raise HTTPException(status_code=400, detail="Location must be 'indoor' or 'balcony'")
        await db.execute("UPDATE plants SET location = ? WHERE id = ?", (body.location, plant_id))
    await db.commit()
    cursor = await db.execute("""
        SELECT p.*, s.interval_days, s.next_watering, s.adjustment_reason
        FROM plants p LEFT JOIN watering_schedules s ON p.id = s.plant_id
        WHERE p.id = ?
    """, (plant_id,))
    row = await cursor.fetchone()
    return _plant_from_row(row)


@router.delete("/{plant_id}", status_code=204)
async def delete_plant(plant_id: int, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT photo_path FROM plants WHERE id = ?", (plant_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Plant not found")

    if row["photo_path"]:
        photo_path = row["photo_path"]
        # Translate web path (/photos/filename) to filesystem path
        if photo_path.startswith("/photos/"):
            photo_path = os.path.join(_get_photo_dir(), os.path.basename(photo_path))
        if os.path.exists(photo_path):
            os.remove(photo_path)

    await db.execute("DELETE FROM plants WHERE id = ?", (plant_id,))
    await db.commit()
