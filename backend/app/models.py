from pydantic import BaseModel
from datetime import datetime


class PlantCreate(BaseModel):
    name: str


class PlantIdentification(BaseModel):
    species: str
    confidence: str
    care_summary: str
    light_preference: str
    base_watering_interval_days: int
    overwatering_signs: str
    underwatering_signs: str


class PlantResponse(BaseModel):
    id: int
    name: str
    species: str | None
    photo_path: str
    identification_details: PlantIdentification | None
    base_watering_interval_days: int | None
    created_at: str
    interval_days: float | None = None
    next_watering: str | None = None
    adjustment_reason: str | None = None


class PlantDetailResponse(PlantResponse):
    watering_logs: list["WateringLogResponse"]


class WateringLogResponse(BaseModel):
    id: int
    watered_at: str
    notes: str | None


class WaterPlantRequest(BaseModel):
    notes: str | None = None


class SettingsResponse(BaseModel):
    location_city: str
    location_latitude: float
    location_longitude: float
    telegram_bot_token_set: bool
    telegram_chat_id: str
    reminder_time: str


class SettingsUpdate(BaseModel):
    location_city: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    reminder_time: str | None = None
