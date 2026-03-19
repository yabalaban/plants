from pydantic import BaseModel


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


class PlantHealth(BaseModel):
    overall: str
    summary: str
    issues: list[str]
    recommendations: list[str]


class PlantResponse(BaseModel):
    id: int
    name: str
    species: str | None
    location: str
    photo_path: str
    identification_details: PlantIdentification | None
    health_status: PlantHealth | None = None
    base_watering_interval_days: int | None
    created_at: str
    interval_days: float | None = None
    next_watering: str | None = None
    adjustment_reason: str | None = None


class PlantUpdate(BaseModel):
    name: str | None = None
    location: str | None = None


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
