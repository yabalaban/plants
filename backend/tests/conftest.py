import os
import pytest
import tempfile
import shutil
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def env_db_path(db_path, monkeypatch):
    monkeypatch.setenv("PLANTS_DB_PATH", db_path)
    return db_path


@pytest.fixture
async def client(env_db_path, tmp_path, monkeypatch):
    photo_dir = str(tmp_path / "photos")
    os.makedirs(photo_dir, exist_ok=True)
    monkeypatch.setenv("PLANTS_PHOTO_DIR", photo_dir)
    monkeypatch.setenv("PLANTS_SETTINGS_PATH", str(tmp_path / "settings.json"))
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def sample_photo(tmp_path):
    """Create a minimal valid JPEG file for testing."""
    photo = tmp_path / "test_plant.jpg"
    photo.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9")
    return photo
