import json
import pytest
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
