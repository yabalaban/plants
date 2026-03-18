import json
import os
from pydantic import BaseModel

_SETTINGS_PATH_DEFAULT = "settings.json"


def _get_settings_path() -> str:
    return os.environ.get("PLANTS_SETTINGS_PATH", _SETTINGS_PATH_DEFAULT)


class LocationSettings(BaseModel):
    city: str = ""
    latitude: float = 0.0
    longitude: float = 0.0


class TelegramSettings(BaseModel):
    bot_token: str = ""
    chat_id: str = ""


class AppSettings(BaseModel):
    location: LocationSettings = LocationSettings()
    telegram: TelegramSettings = TelegramSettings()
    reminder_time: str = "09:00"
    photo_dir: str = "./photos"


def load_settings() -> AppSettings:
    path = _get_settings_path()
    if not os.path.exists(path):
        return AppSettings()
    with open(path) as f:
        return AppSettings(**json.load(f))


def save_settings(settings: AppSettings) -> None:
    path = _get_settings_path()
    with open(path, "w") as f:
        json.dump(settings.model_dump(), f, indent=2)
