from fastapi import APIRouter, HTTPException
from app.models import SettingsResponse, SettingsUpdate
from app.settings import load_settings, save_settings
from app.services.telegram import send_message
from app.services.weather import geocode_city

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings():
    s = load_settings()
    return SettingsResponse(location_city=s.location.city, location_latitude=s.location.latitude,
        location_longitude=s.location.longitude, telegram_bot_token_set=bool(s.telegram.bot_token),
        telegram_chat_id=s.telegram.chat_id, reminder_time=s.reminder_time)


@router.put("", response_model=SettingsResponse)
async def update_settings(body: SettingsUpdate):
    s = load_settings()
    if body.location_city is not None:
        s.location.city = body.location_city
        coords = await geocode_city(body.location_city)
        if coords:
            s.location.latitude, s.location.longitude = coords
    if body.telegram_bot_token is not None:
        s.telegram.bot_token = body.telegram_bot_token
    if body.telegram_chat_id is not None:
        s.telegram.chat_id = body.telegram_chat_id
    if body.reminder_time is not None:
        s.reminder_time = body.reminder_time
    save_settings(s)
    return SettingsResponse(location_city=s.location.city, location_latitude=s.location.latitude,
        location_longitude=s.location.longitude, telegram_bot_token_set=bool(s.telegram.bot_token),
        telegram_chat_id=s.telegram.chat_id, reminder_time=s.reminder_time)


@router.post("/test-telegram")
async def test_telegram():
    s = load_settings()
    if not s.telegram.bot_token or not s.telegram.chat_id:
        raise HTTPException(status_code=400, detail="Telegram not configured")
    success = await send_message(s.telegram.bot_token, s.telegram.chat_id,
        "Plant Tracker: test message! Your Telegram notifications are working.")
    if not success:
        raise HTTPException(status_code=502, detail="Failed to send Telegram message")
    return {"status": "sent"}
