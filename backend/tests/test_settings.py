import json
import pytest
from unittest.mock import AsyncMock, patch
from app.settings import AppSettings, load_settings, save_settings


def test_load_settings_returns_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setenv("PLANTS_SETTINGS_PATH", str(tmp_path / "settings.json"))
    settings = load_settings()
    assert settings.location.city == ""
    assert settings.reminder_time == "09:00"
    assert settings.photo_dir == "./photos"


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    path = str(tmp_path / "settings.json")
    monkeypatch.setenv("PLANTS_SETTINGS_PATH", path)
    settings = AppSettings()
    settings.location.city = "Amsterdam"
    settings.location.latitude = 52.37
    settings.location.longitude = 4.89
    settings.telegram.bot_token = "test-token"
    settings.telegram.chat_id = "12345"
    save_settings(settings)
    loaded = load_settings()
    assert loaded.location.city == "Amsterdam"
    assert loaded.location.latitude == 52.37
    assert loaded.telegram.bot_token == "test-token"
    assert loaded.reminder_time == "09:00"


def test_save_creates_file(tmp_path, monkeypatch):
    path = str(tmp_path / "settings.json")
    monkeypatch.setenv("PLANTS_SETTINGS_PATH", path)
    save_settings(AppSettings())
    with open(path) as f:
        data = json.load(f)
    assert "location" in data
    assert "telegram" in data


@pytest.mark.asyncio
async def test_get_settings_api(client):
    resp = await client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["location_city"] == ""
    assert data["reminder_time"] == "09:00"
    assert data["telegram_bot_token_set"] is False


@pytest.mark.asyncio
async def test_update_settings_api(client):
    with patch("app.routers.settings_router.geocode_city", new=AsyncMock(return_value=(52.37, 4.89))):
        resp = await client.put("/api/settings", json={
            "location_city": "Amsterdam",
            "telegram_bot_token": "test-token-123",
            "telegram_chat_id": "99999",
            "reminder_time": "08:30",
        })
    assert resp.status_code == 200
    resp = await client.get("/api/settings")
    data = resp.json()
    assert data["location_city"] == "Amsterdam"
    assert data["telegram_bot_token_set"] is True
    assert data["telegram_chat_id"] == "99999"


@pytest.mark.asyncio
async def test_test_telegram_without_config(client):
    resp = await client.post("/api/settings/test-telegram")
    assert resp.status_code == 400
