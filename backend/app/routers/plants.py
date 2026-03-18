import json
import os
import shutil
import uuid
from datetime import datetime

import aiosqlite
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.database import get_db
from app.models import PlantDetailResponse, PlantResponse, WaterPlantRequest, WateringLogResponse

router = APIRouter(prefix="/api/plants", tags=["plants"])


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

    cursor = await db.execute(
        "INSERT INTO plants (name, photo_path) VALUES (?, ?)",
        (name, filepath),
    )
    await db.commit()
    plant_id = cursor.lastrowid

    cursor = await db.execute("SELECT * FROM plants WHERE id = ?", (plant_id,))
    row = await cursor.fetchone()
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

    if row["photo_path"] and os.path.exists(row["photo_path"]):
        os.remove(row["photo_path"])

    await db.execute("DELETE FROM plants WHERE id = ?", (plant_id,))
    await db.commit()
