import asyncio
import json
import os
import shutil
import uuid
from datetime import datetime

import aiosqlite
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.database import get_db
from app.models import PlantDetailResponse, PlantResponse, WaterPlantRequest, WateringLogResponse
from app.services.claude import identify_plant

router = APIRouter(prefix="/api/plants", tags=["plants"])


async def _identify_and_update(plant_id: int, photo_path: str):
    from app.database import get_db_path
    identification = await identify_plant(photo_path)
    if not identification:
        return
    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        db.row_factory = aiosqlite.Row
        await db.execute("""
            UPDATE plants SET species = ?, identification_details = ?, base_watering_interval_days = ?
            WHERE id = ?
        """, (identification.get("species"), json.dumps(identification),
              identification.get("base_watering_interval_days", 7), plant_id))
        interval = identification.get("base_watering_interval_days", 7)
        await db.execute("""
            INSERT OR REPLACE INTO watering_schedules (plant_id, interval_days, next_watering, adjustment_reason)
            VALUES (?, ?, datetime('now', '+' || ? || ' days'), 'initial schedule')
        """, (plant_id, interval, interval))
        await db.commit()


def _get_photo_dir() -> str:
    return os.environ.get("PLANTS_PHOTO_DIR", "./photos")


@router.get("", response_model=list[PlantResponse])
async def list_plants(db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("""
        SELECT p.*, s.interval_days, s.next_watering, s.adjustment_reason
        FROM plants p
        LEFT JOIN watering_schedules s ON p.id = s.plant_id
        ORDER BY s.next_watering ASC NULLS LAST
    """)
    rows = await cursor.fetchall()
    plants = []
    for row in rows:
        identification = None
        if row["identification_details"]:
            identification = json.loads(row["identification_details"])
        plants.append(PlantResponse(
            id=row["id"],
            name=row["name"],
            species=row["species"],
            photo_path=row["photo_path"],
            identification_details=identification,
            base_watering_interval_days=row["base_watering_interval_days"],
            created_at=row["created_at"],
            interval_days=row["interval_days"],
            next_watering=row["next_watering"],
            adjustment_reason=row["adjustment_reason"],
        ))
    return plants


@router.post("", response_model=PlantResponse, status_code=201)
async def add_plant(
    name: str = Form(...),
    photo: UploadFile = File(...),
    db: aiosqlite.Connection = Depends(get_db),
):
    photo_dir = _get_photo_dir()
    os.makedirs(photo_dir, exist_ok=True)
    ext = os.path.splitext(photo.filename or "photo.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(photo_dir, filename)

    with open(filepath, "wb") as f:
        content = await photo.read()
        f.write(content)

    web_path = f"/photos/{filename}"
    cursor = await db.execute(
        "INSERT INTO plants (name, photo_path) VALUES (?, ?)",
        (name, web_path),
    )
    await db.commit()
    plant_id = cursor.lastrowid

    cursor = await db.execute("SELECT * FROM plants WHERE id = ?", (plant_id,))
    row = await cursor.fetchone()
    asyncio.create_task(_identify_and_update(plant_id, filepath))
    return PlantResponse(
        id=row["id"],
        name=row["name"],
        species=row["species"],
        photo_path=row["photo_path"],
        identification_details=None,
        base_watering_interval_days=row["base_watering_interval_days"],
        created_at=row["created_at"],
    )


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

    identification = None
    if row["identification_details"]:
        identification = json.loads(row["identification_details"])

    return PlantDetailResponse(
        id=row["id"],
        name=row["name"],
        species=row["species"],
        photo_path=row["photo_path"],
        identification_details=identification,
        base_watering_interval_days=row["base_watering_interval_days"],
        created_at=row["created_at"],
        interval_days=row["interval_days"],
        next_watering=row["next_watering"],
        adjustment_reason=row["adjustment_reason"],
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
        SET next_watering = datetime('now', '+' || CAST(interval_days AS INTEGER) || ' days')
        WHERE plant_id = ?
    """, (plant_id,))
    await db.commit()
    return {"status": "logged"}


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
