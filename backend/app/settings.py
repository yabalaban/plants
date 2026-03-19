import json
import os
from pydantic import BaseModel

_SETTINGS_PATH_DEFAULT = "settings.json"


def _get_settings_path() -> str:
    return os.environ.get("PLANTS_SETTINGS_PATH", _SETTINGS_PATH_DEFAULT)


def _read_secret(name: str) -> str | None:
    """Read a Podman/Docker secret from /run/secrets/."""
    path = f"/run/secrets/{name}"
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


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
    if os.path.exists(path):
        with open(path) as f:
            settings = AppSettings(**json.load(f))
    else:
        settings = AppSettings()

    # Override with Podman secrets if available
    token = _read_secret("telegram_bot_token")
    if token:
        settings.telegram.bot_token = token
    chat_id = _read_secret("telegram_chat_id")
    if chat_id:
        settings.telegram.chat_id = chat_id

    return settings


def save_settings(settings: AppSettings) -> None:
    path = _get_settings_path()
    with open(path, "w") as f:
        json.dump(settings.model_dump(), f, indent=2)
