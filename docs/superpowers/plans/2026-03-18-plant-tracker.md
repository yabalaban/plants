# Plant Life Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a personal mobile-first PWA for tracking houseplants with Claude CLI-powered identification and weather-adaptive watering schedules.

**Architecture:** FastAPI backend serving a compiled SvelteKit PWA as static files, with SQLite for storage, APScheduler for background jobs, Claude CLI for plant intelligence, Open-Meteo for weather, and Telegram for push notifications. Single process on Raspberry Pi, accessed via VPN over plain HTTP.

**Tech Stack:** Python 3.11+, FastAPI, aiosqlite, APScheduler, httpx, SvelteKit, TypeScript, SQLite, Claude CLI, Open-Meteo API, Telegram Bot API

**Tooling:** Use `mise` for managing tool versions (Python, Node.js, uv). Use `uv` for all Python dependency management. If `uv` is not available, install it via `mise`.

**Spec:** `docs/superpowers/specs/2026-03-18-plant-tracker-design.md`

---

## File Structure

```
plants/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app, lifespan, static serving
│   │   ├── database.py                # SQLite connection + schema init
│   │   ├── models.py                  # Pydantic request/response models
│   │   ├── settings.py                # settings.json read/write
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── plants.py              # Plant CRUD + watering endpoints
│   │   │   └── settings_router.py     # Settings endpoints
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── claude.py              # Claude CLI subprocess wrapper
│   │       ├── weather.py             # Open-Meteo API client
│   │       ├── telegram.py            # Telegram Bot API client
│   │       ├── scheduler.py           # APScheduler setup + job definitions
│   │       └── watering.py            # Watering schedule calculation
│   ├── tests/
│   │   ├── conftest.py                # Shared fixtures (test DB, test client)
│   │   ├── test_database.py
│   │   ├── test_settings.py
│   │   ├── test_plants_api.py
│   │   ├── test_claude.py
│   │   ├── test_weather.py
│   │   ├── test_telegram.py
│   │   └── test_watering.py
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app.html
│   │   ├── app.css                    # Global styles
│   │   ├── lib/
│   │   │   ├── api.ts                 # API client functions
│   │   │   └── types.ts               # TypeScript interfaces
│   │   └── routes/
│   │       ├── +layout.svelte         # App shell + bottom nav
│   │       ├── +page.svelte           # Dashboard
│   │       ├── add/+page.svelte       # Add Plant
│   │       ├── plants/[id]/+page.svelte  # Plant Detail
│   │       └── settings/+page.svelte  # Settings
│   ├── static/
│   │   └── manifest.json              # PWA manifest
│   ├── svelte.config.js
│   ├── vite.config.ts
│   ├── package.json
│   └── tsconfig.json
├── .mise.toml                         # Tool versions (Python, Node, uv)
├── settings.json                      # Runtime config (created on first run)
└── photos/                            # Plant photo storage
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `.mise.toml`, `.gitignore`
- Create: `backend/app/__init__.py`, `backend/app/main.py`, `backend/pyproject.toml`
- Create: `backend/app/routers/__init__.py`, `backend/app/services/__init__.py`
- Create: `frontend/package.json`, `frontend/svelte.config.js`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/src/app.html`

- [ ] **Step 1: Create .mise.toml for tool versions**

```toml
[tools]
python = "3.12"
node = "22"
uv = "latest"
```

- [ ] **Step 2: Install tools via mise**

Run: `mise install`

This installs Python, Node.js, and uv. Verify:
Run: `mise exec -- uv --version && mise exec -- node --version && mise exec -- python --version`

- [ ] **Step 3: Create .gitignore**

```gitignore
__pycache__/
*.pyc
.pytest_cache/
plants.db
settings.json
photos/
node_modules/
frontend/build/
frontend/.svelte-kit/
.superpowers/
.venv/
```

- [ ] **Step 4: Create backend Python package structure**

Create `backend/app/__init__.py` (empty file).
Create `backend/app/routers/__init__.py` (empty file).
Create `backend/app/services/__init__.py` (empty file).

- [ ] **Step 5: Create pyproject.toml**

`backend/pyproject.toml`:
```toml
[project]
name = "plant-tracker"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.6",
    "uvicorn[standard]>=0.34.0",
    "aiosqlite>=0.20.0",
    "httpx>=0.28.1",
    "apscheduler>=3.10.4",
    "python-multipart>=0.0.20",
    "pydantic>=2.10.4",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
]
```

- [ ] **Step 6: Create minimal FastAPI app**

`backend/app/main.py`:
```python
from fastapi import FastAPI

app = FastAPI(title="Plant Tracker")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 7: Install backend dependencies with uv**

Run: `cd backend && uv sync`

This creates the venv and installs all dependencies (including dev deps).

- [ ] **Step 8: Verify backend starts**

Run: `cd backend && uv run uvicorn app.main:app --port 8000 &`
Then: `curl http://localhost:8000/api/health`
Expected: `{"status":"ok"}`
Kill the server after verification.

- [ ] **Step 9: Scaffold SvelteKit frontend**

Run: `cd frontend && npm create svelte@latest . -- --template skeleton --types typescript`

Then install adapter-static:
Run: `cd frontend && npm install && npm install -D @sveltejs/adapter-static`

- [ ] **Step 10: Configure SvelteKit for static build**

`frontend/svelte.config.js`:
```javascript
import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter({
			pages: 'build',
			assets: 'build',
			fallback: 'index.html'
		})
	}
};

export default config;
```

- [ ] **Step 11: Add prerender config**

`frontend/src/routes/+layout.ts`:
```typescript
export const prerender = false;
export const ssr = false;
```

- [ ] **Step 12: Verify frontend builds**

Run: `cd frontend && npm run build`
Expected: Build succeeds, `frontend/build/` directory created.

- [ ] **Step 13: Commit**

```bash
git add -A
git commit -m "feat: scaffold project structure (FastAPI + SvelteKit)"
```

---

## Task 2: Database Layer

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/tests/conftest.py`, `backend/tests/test_database.py`

- [ ] **Step 1: Write database tests**

`backend/tests/conftest.py`:
```python
import os
import pytest
import tempfile


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def env_db_path(db_path, monkeypatch):
    monkeypatch.setenv("PLANTS_DB_PATH", db_path)
    return db_path
```

`backend/tests/test_database.py`:
```python
import pytest
import aiosqlite
from app.database import init_db, get_db_path


@pytest.mark.asyncio
async def test_init_db_creates_tables(env_db_path):
    await init_db()
    async with aiosqlite.connect(env_db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in await cursor.fetchall()]
    assert "plants" in tables
    assert "watering_logs" in tables
    assert "watering_schedules" in tables
    assert "weather_cache" in tables


@pytest.mark.asyncio
async def test_foreign_keys_enabled(env_db_path):
    await init_db()
    async with aiosqlite.connect(env_db_path) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        # Insert a plant
        await db.execute(
            "INSERT INTO plants (name, photo_path) VALUES (?, ?)",
            ("Test", "/tmp/test.jpg"),
        )
        await db.commit()
        # Insert a watering log
        await db.execute(
            "INSERT INTO watering_logs (plant_id, watered_at) VALUES (1, CURRENT_TIMESTAMP)"
        )
        await db.commit()
        # Delete the plant — should cascade
        await db.execute("DELETE FROM plants WHERE id = 1")
        await db.commit()
        cursor = await db.execute("SELECT COUNT(*) FROM watering_logs")
        count = (await cursor.fetchone())[0]
    assert count == 0


@pytest.mark.asyncio
async def test_init_db_idempotent(env_db_path):
    await init_db()
    await init_db()  # Should not raise
    async with aiosqlite.connect(env_db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in await cursor.fetchall()]
    assert "plants" in tables
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_database.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.database'`

- [ ] **Step 3: Implement database module**

`backend/app/database.py`:
```python
import os
import aiosqlite

_DB_PATH_DEFAULT = "plants.db"


def get_db_path() -> str:
    return os.environ.get("PLANTS_DB_PATH", _DB_PATH_DEFAULT)


async def get_db():
    db = await aiosqlite.connect(get_db_path())
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
    finally:
        await db.close()


async def init_db():
    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                species TEXT,
                photo_path TEXT NOT NULL,
                identification_details TEXT,
                base_watering_interval_days INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS watering_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id INTEGER NOT NULL
                    REFERENCES plants(id) ON DELETE CASCADE,
                watered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS watering_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id INTEGER NOT NULL UNIQUE
                    REFERENCES plants(id) ON DELETE CASCADE,
                interval_days REAL NOT NULL,
                next_watering TIMESTAMP NOT NULL,
                last_adjusted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                adjustment_reason TEXT
            );

            CREATE TABLE IF NOT EXISTS weather_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,
                temp_high REAL,
                temp_low REAL,
                humidity REAL,
                precipitation_mm REAL,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await db.commit()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_database.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/database.py backend/tests/conftest.py backend/tests/test_database.py
git commit -m "feat: add SQLite database layer with schema init"
```

---

## Task 3: Settings Management

**Files:**
- Create: `backend/app/settings.py`
- Create: `backend/tests/test_settings.py`

- [ ] **Step 1: Write settings tests**

`backend/tests/test_settings.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_settings.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement settings module**

`backend/app/settings.py`:
```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_settings.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/settings.py backend/tests/test_settings.py
git commit -m "feat: add settings management (settings.json read/write)"
```

---

## Task 4: Pydantic Models

**Files:**
- Create: `backend/app/models.py`

- [ ] **Step 1: Create API models**

`backend/app/models.py`:
```python
from pydantic import BaseModel
from datetime import datetime


# --- Plants ---

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
    # Schedule info (joined)
    interval_days: float | None = None
    next_watering: str | None = None
    adjustment_reason: str | None = None


class PlantDetailResponse(PlantResponse):
    watering_logs: list["WateringLogResponse"]


# --- Watering ---

class WateringLogResponse(BaseModel):
    id: int
    watered_at: str
    notes: str | None


class WaterPlantRequest(BaseModel):
    notes: str | None = None


# --- Settings ---

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
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models.py
git commit -m "feat: add Pydantic request/response models"
```

---

## Task 5: Plant CRUD API

**Files:**
- Create: `backend/app/routers/plants.py`
- Create: `backend/tests/test_plants_api.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add test fixtures for API testing**

Add to `backend/tests/conftest.py`:
```python
import shutil
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db


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
    # Minimal JPEG: SOI marker + EOI marker
    photo.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9")
    return photo
```

- [ ] **Step 2: Write plant API tests**

`backend/tests/test_plants_api.py`:
```python
import pytest


@pytest.mark.asyncio
async def test_list_plants_empty(client):
    resp = await client.get("/api/plants")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_add_plant(client, sample_photo):
    with open(sample_photo, "rb") as f:
        resp = await client.post(
            "/api/plants",
            data={"name": "My Monstera"},
            files={"photo": ("plant.jpg", f, "image/jpeg")},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Monstera"
    assert data["id"] == 1
    assert data["species"] is None  # Not yet identified


@pytest.mark.asyncio
async def test_get_plant_detail(client, sample_photo):
    with open(sample_photo, "rb") as f:
        await client.post(
            "/api/plants",
            data={"name": "My Fern"},
            files={"photo": ("fern.jpg", f, "image/jpeg")},
        )
    resp = await client.get("/api/plants/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "My Fern"
    assert data["watering_logs"] == []


@pytest.mark.asyncio
async def test_get_plant_not_found(client):
    resp = await client.get("/api/plants/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_plant(client, sample_photo):
    with open(sample_photo, "rb") as f:
        await client.post(
            "/api/plants",
            data={"name": "Doomed Plant"},
            files={"photo": ("plant.jpg", f, "image/jpeg")},
        )
    resp = await client.delete("/api/plants/1")
    assert resp.status_code == 204
    resp = await client.get("/api/plants")
    assert resp.json() == []


@pytest.mark.asyncio
async def test_water_plant(client, sample_photo):
    with open(sample_photo, "rb") as f:
        await client.post(
            "/api/plants",
            data={"name": "Thirsty Plant"},
            files={"photo": ("plant.jpg", f, "image/jpeg")},
        )
    resp = await client.post("/api/plants/1/water", json={"notes": "Looked dry"})
    assert resp.status_code == 201

    resp = await client.get("/api/plants/1")
    assert len(resp.json()["watering_logs"]) == 1
    assert resp.json()["watering_logs"][0]["notes"] == "Looked dry"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_plants_api.py -v`
Expected: FAIL

- [ ] **Step 4: Implement plants router**

`backend/app/routers/plants.py`:
```python
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
            WateringLogResponse(
                id=log["id"],
                watered_at=log["watered_at"],
                notes=log["notes"],
            )
            for log in logs
        ],
    )


@router.post("/{plant_id}/water", status_code=201)
async def water_plant(
    plant_id: int,
    body: WaterPlantRequest,
    db: aiosqlite.Connection = Depends(get_db),
):
    cursor = await db.execute("SELECT id FROM plants WHERE id = ?", (plant_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Plant not found")

    await db.execute(
        "INSERT INTO watering_logs (plant_id, notes) VALUES (?, ?)",
        (plant_id, body.notes),
    )

    # Update next_watering if schedule exists
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

    # Delete photo file
    if row["photo_path"] and os.path.exists(row["photo_path"]):
        os.remove(row["photo_path"])

    await db.execute("DELETE FROM plants WHERE id = ?", (plant_id,))
    await db.commit()
```

- [ ] **Step 5: Wire router into main app**

Replace `backend/app/main.py`:
```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import plants


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Plant Tracker", lifespan=lifespan)
app.include_router(plants.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_plants_api.py -v`
Expected: All 5 tests PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/plants.py backend/app/main.py backend/app/models.py backend/tests/conftest.py backend/tests/test_plants_api.py
git commit -m "feat: add plant CRUD API with photo upload and watering log"
```

---

## Task 6: Claude CLI Integration

**Files:**
- Create: `backend/app/services/claude.py`
- Create: `backend/tests/test_claude.py`
- Modify: `backend/app/routers/plants.py` (trigger identification on add)

- [ ] **Step 1: Write Claude service tests**

`backend/tests/test_claude.py`:
```python
import json
import pytest
from unittest.mock import AsyncMock, patch
from app.services.claude import identify_plant, adjust_schedules


MOCK_IDENTIFICATION = {
    "species": "Monstera deliciosa",
    "confidence": "high",
    "care_summary": "Tropical plant that likes indirect light and moderate watering.",
    "light_preference": "bright indirect",
    "base_watering_interval_days": 7,
    "overwatering_signs": "Yellow leaves, mushy stems",
    "underwatering_signs": "Brown crispy leaf edges, drooping"
}


@pytest.mark.asyncio
async def test_identify_plant_parses_json():
    mock_result = json.dumps(MOCK_IDENTIFICATION)
    with patch("app.services.claude._run_claude_cli", return_value=mock_result):
        result = await identify_plant("/tmp/photo.jpg")
    assert result["species"] == "Monstera deliciosa"
    assert result["base_watering_interval_days"] == 7


@pytest.mark.asyncio
async def test_identify_plant_handles_markdown_fenced_json():
    mock_result = f"```json\n{json.dumps(MOCK_IDENTIFICATION)}\n```"
    with patch("app.services.claude._run_claude_cli", return_value=mock_result):
        result = await identify_plant("/tmp/photo.jpg")
    assert result["species"] == "Monstera deliciosa"


@pytest.mark.asyncio
async def test_identify_plant_returns_none_on_failure():
    with patch("app.services.claude._run_claude_cli", side_effect=RuntimeError("CLI failed")):
        result = await identify_plant("/tmp/photo.jpg")
    assert result is None


@pytest.mark.asyncio
async def test_adjust_schedules_returns_adjustments():
    mock_response = json.dumps([
        {"plant_id": 1, "interval_days": 5, "reason": "Hot weather this week"}
    ])
    with patch("app.services.claude._run_claude_cli", return_value=mock_response):
        result = await adjust_schedules(
            plants=[{"id": 1, "species": "Monstera", "interval_days": 7}],
            weather=[{"date": "2026-03-15", "temp_high": 32, "humidity": 40}],
        )
    assert len(result) == 1
    assert result[0]["interval_days"] == 5
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_claude.py -v`
Expected: FAIL

- [ ] **Step 3: Implement Claude CLI service**

`backend/app/services/claude.py`:
```python
import asyncio
import json
import logging
import re

logger = logging.getLogger(__name__)


async def _run_claude_cli(prompt: str, image_path: str | None = None) -> str:
    cmd = ["claude", "-p", prompt, "--output-format", "text"]
    if image_path:
        cmd.extend(["--files", image_path])

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"Claude CLI failed: {stderr.decode()}")

    return stdout.decode().strip()


def _extract_json(text: str) -> dict | list:
    """Extract JSON from Claude's response, handling markdown fences."""
    # Try to find JSON in markdown code fences
    fence_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
    if fence_match:
        return json.loads(fence_match.group(1).strip())
    # Try parsing the whole response as JSON
    return json.loads(text)


async def identify_plant(photo_path: str) -> dict | None:
    prompt = (
        "Identify this plant from the photo. Return ONLY valid JSON (no other text) "
        "with these fields: species (string, common and Latin name), "
        "confidence (string: high/medium/low), "
        "care_summary (string, 1-2 sentences), "
        "light_preference (string), "
        "base_watering_interval_days (integer, for indoor conditions), "
        "overwatering_signs (string), underwatering_signs (string)."
    )
    try:
        response = await _run_claude_cli(prompt, image_path=photo_path)
        return _extract_json(response)
    except Exception:
        logger.exception("Plant identification failed")
        return None


async def adjust_schedules(
    plants: list[dict], weather: list[dict]
) -> list[dict]:
    prompt = (
        "Given these plants and their current watering schedules:\n"
        f"{json.dumps(plants, indent=2)}\n\n"
        "And this week's weather data:\n"
        f"{json.dumps(weather, indent=2)}\n\n"
        "Return ONLY valid JSON: an array of objects with plant_id (int), "
        "interval_days (number, adjusted watering interval in days), "
        "and reason (string, why the adjustment was made). "
        "If no adjustment is needed for a plant, keep the same interval_days "
        "and set reason to 'no change needed'."
    )
    try:
        response = await _run_claude_cli(prompt)
        return _extract_json(response)
    except Exception:
        logger.exception("Schedule adjustment failed")
        return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_claude.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Add background identification trigger to plants router**

Add to the top of `backend/app/routers/plants.py`:
```python
import asyncio
from app.services.claude import identify_plant
```

Add a helper function after the imports:
```python
async def _identify_and_update(plant_id: int, photo_path: str):
    """Background task: identify plant via Claude CLI and update DB."""
    from app.database import get_db_path
    identification = await identify_plant(photo_path)
    if not identification:
        return

    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        db.row_factory = aiosqlite.Row
        await db.execute("""
            UPDATE plants
            SET species = ?,
                identification_details = ?,
                base_watering_interval_days = ?
            WHERE id = ?
        """, (
            identification.get("species"),
            json.dumps(identification),
            identification.get("base_watering_interval_days", 7),
            plant_id,
        ))
        # Create initial watering schedule
        interval = identification.get("base_watering_interval_days", 7)
        await db.execute("""
            INSERT OR REPLACE INTO watering_schedules
                (plant_id, interval_days, next_watering, adjustment_reason)
            VALUES (?, ?, datetime('now', '+' || ? || ' days'), 'initial schedule')
        """, (plant_id, interval, interval))
        await db.commit()
```

In the `add_plant` endpoint, add before the `return` statement:
```python
    # Trigger identification in background
    asyncio.create_task(_identify_and_update(plant_id, filepath))
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/claude.py backend/tests/test_claude.py backend/app/routers/plants.py
git commit -m "feat: add Claude CLI integration for plant identification"
```

---

## Task 7: Weather Service

**Files:**
- Create: `backend/app/services/weather.py`
- Create: `backend/tests/test_weather.py`

- [ ] **Step 1: Write weather service tests**

`backend/tests/test_weather.py`:
```python
import json
import pytest
from unittest.mock import AsyncMock, patch
from app.services.weather import fetch_weather, geocode_city


MOCK_GEOCODE_RESPONSE = {
    "results": [
        {"name": "Amsterdam", "latitude": 52.374, "longitude": 4.8897}
    ]
}

MOCK_WEATHER_RESPONSE = {
    "daily": {
        "time": ["2026-03-18"],
        "temperature_2m_max": [18.5],
        "temperature_2m_min": [8.2],
        "relative_humidity_2m_mean": [72.0],
        "precipitation_sum": [0.0],
    }
}


@pytest.mark.asyncio
async def test_geocode_city():
    mock_response = AsyncMock()
    mock_response.json.return_value = MOCK_GEOCODE_RESPONSE
    mock_response.raise_for_status = lambda: None

    with patch("app.services.weather.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        lat, lon = await geocode_city("Amsterdam")
    assert abs(lat - 52.374) < 0.01
    assert abs(lon - 4.8897) < 0.01


@pytest.mark.asyncio
async def test_geocode_city_not_found():
    mock_response = AsyncMock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = lambda: None

    with patch("app.services.weather.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        result = await geocode_city("Nonexistentville")
    assert result is None


@pytest.mark.asyncio
async def test_fetch_weather():
    mock_response = AsyncMock()
    mock_response.json.return_value = MOCK_WEATHER_RESPONSE
    mock_response.raise_for_status = lambda: None

    with patch("app.services.weather.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        days = await fetch_weather(52.374, 4.8897)
    assert len(days) == 1
    assert days[0]["date"] == "2026-03-18"
    assert days[0]["temp_high"] == 18.5
    assert days[0]["precipitation_mm"] == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_weather.py -v`
Expected: FAIL

- [ ] **Step 3: Implement weather service**

`backend/app/services/weather.py`:
```python
import logging
import httpx

logger = logging.getLogger(__name__)

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


async def geocode_city(city: str) -> tuple[float, float] | None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(GEOCODE_URL, params={"name": city, "count": 1})
        resp.raise_for_status()
        data = resp.json()
    results = data.get("results", [])
    if not results:
        return None
    return results[0]["latitude"], results[0]["longitude"]


async def fetch_weather(
    latitude: float, longitude: float, days: int = 7
) -> list[dict]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,relative_humidity_2m_mean,precipitation_sum",
        "past_days": days,
        "forecast_days": 1,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(WEATHER_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    daily = data["daily"]
    result = []
    for i, date in enumerate(daily["time"]):
        result.append({
            "date": date,
            "temp_high": daily["temperature_2m_max"][i],
            "temp_low": daily["temperature_2m_min"][i],
            "humidity": daily["relative_humidity_2m_mean"][i],
            "precipitation_mm": daily["precipitation_sum"][i],
        })
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_weather.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/weather.py backend/tests/test_weather.py
git commit -m "feat: add Open-Meteo weather service with geocoding"
```

---

## Task 8: Telegram Notification Service

**Files:**
- Create: `backend/app/services/telegram.py`
- Create: `backend/tests/test_telegram.py`

- [ ] **Step 1: Write Telegram service tests**

`backend/tests/test_telegram.py`:
```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.telegram import send_message, format_watering_reminder


def test_format_watering_reminder_single():
    plants = [{"name": "Monstera", "status": "due"}]
    msg = format_watering_reminder(plants)
    assert "Monstera" in msg
    assert "water" in msg.lower()


def test_format_watering_reminder_multiple():
    plants = [
        {"name": "Monstera", "status": "due"},
        {"name": "Fern", "status": "overdue"},
    ]
    msg = format_watering_reminder(plants)
    assert "Monstera" in msg
    assert "Fern" in msg
    assert "overdue" in msg.lower()


def test_format_watering_reminder_empty():
    msg = format_watering_reminder([])
    assert msg is None


@pytest.mark.asyncio
async def test_send_message():
    mock_response = AsyncMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {"ok": True}

    with patch("app.services.telegram.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        result = await send_message("test-token", "12345", "Hello!")
    assert result is True


@pytest.mark.asyncio
async def test_send_message_failure():
    with patch("app.services.telegram.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("Network error")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        result = await send_message("test-token", "12345", "Hello!")
    assert result is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_telegram.py -v`
Expected: FAIL

- [ ] **Step 3: Implement Telegram service**

`backend/app/services/telegram.py`:
```python
import logging
import httpx

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


async def send_message(bot_token: str, chat_id: str, text: str) -> bool:
    url = f"{TELEGRAM_API}/bot{bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            })
            resp.raise_for_status()
        return True
    except Exception:
        logger.exception("Failed to send Telegram message")
        return False


def format_watering_reminder(plants: list[dict]) -> str | None:
    if not plants:
        return None

    lines = ["*Time to water your plants!*\n"]
    for p in plants:
        status = p["status"]
        emoji = "!" if status == "overdue" else ""
        label = f" (overdue{emoji})" if status == "overdue" else ""
        lines.append(f"- {p['name']}{label}")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_telegram.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/telegram.py backend/tests/test_telegram.py
git commit -m "feat: add Telegram notification service"
```

---

## Task 9: Watering Schedule Logic

**Files:**
- Create: `backend/app/services/watering.py`
- Create: `backend/tests/test_watering.py`

- [ ] **Step 1: Write watering schedule tests**

`backend/tests/test_watering.py`:
```python
import pytest
from datetime import datetime, timedelta
from app.services.watering import get_plants_needing_water, compute_next_watering


def test_compute_next_watering():
    now = datetime(2026, 3, 18, 9, 0)
    result = compute_next_watering(interval_days=5, from_time=now)
    assert result == datetime(2026, 3, 23, 9, 0)


def test_compute_next_watering_fractional():
    now = datetime(2026, 3, 18, 9, 0)
    result = compute_next_watering(interval_days=3.5, from_time=now)
    expected = now + timedelta(days=3.5)
    assert result == expected


@pytest.mark.asyncio
async def test_get_plants_needing_water(env_db_path):
    import aiosqlite
    from app.database import init_db

    await init_db()
    async with aiosqlite.connect(env_db_path) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        # Add a plant
        await db.execute(
            "INSERT INTO plants (name, photo_path) VALUES (?, ?)",
            ("Thirsty", "/tmp/t.jpg"),
        )
        # Add overdue schedule
        await db.execute("""
            INSERT INTO watering_schedules (plant_id, interval_days, next_watering)
            VALUES (1, 5, datetime('now', '-1 day'))
        """)
        # Add a plant not yet due
        await db.execute(
            "INSERT INTO plants (name, photo_path) VALUES (?, ?)",
            ("Happy", "/tmp/h.jpg"),
        )
        await db.execute("""
            INSERT INTO watering_schedules (plant_id, interval_days, next_watering)
            VALUES (2, 7, datetime('now', '+3 days'))
        """)
        await db.commit()

        due = await get_plants_needing_water(db)
    assert len(due) == 1
    assert due[0]["name"] == "Thirsty"
    assert due[0]["status"] == "overdue"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_watering.py -v`
Expected: FAIL

- [ ] **Step 3: Implement watering logic**

`backend/app/services/watering.py`:
```python
from datetime import datetime, timedelta

import aiosqlite


def compute_next_watering(
    interval_days: float, from_time: datetime | None = None
) -> datetime:
    base = from_time or datetime.now()
    return base + timedelta(days=interval_days)


async def get_plants_needing_water(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute("""
        SELECT p.id, p.name, s.next_watering, s.interval_days
        FROM plants p
        JOIN watering_schedules s ON p.id = s.plant_id
        WHERE s.next_watering <= datetime('now')
        ORDER BY s.next_watering ASC
    """)
    rows = await cursor.fetchall()
    result = []
    for row in rows:
        next_dt = datetime.fromisoformat(row["next_watering"])
        now = datetime.now()
        if next_dt.date() < now.date():
            status = "overdue"
        else:
            status = "due"
        result.append({
            "id": row["id"],
            "name": row["name"],
            "next_watering": row["next_watering"],
            "interval_days": row["interval_days"],
            "status": status,
        })
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_watering.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/watering.py backend/tests/test_watering.py
git commit -m "feat: add watering schedule logic"
```

---

## Task 10: Settings Router

**Files:**
- Create: `backend/app/routers/settings_router.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write settings API tests**

Add to `backend/tests/test_settings.py`:
```python
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
    assert data["reminder_time"] == "08:30"


@pytest.mark.asyncio
async def test_test_telegram_without_config(client):
    resp = await client.post("/api/settings/test-telegram")
    assert resp.status_code == 400
```

Add imports at top of `test_settings.py`:
```python
import os
import pytest
```

Add the `client` fixture import — it's already in `conftest.py`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_settings.py -v`
Expected: New API tests FAIL (404)

- [ ] **Step 3: Implement settings router**

`backend/app/routers/settings_router.py`:
```python
from fastapi import APIRouter, HTTPException

from app.models import SettingsResponse, SettingsUpdate
from app.settings import load_settings, save_settings
from app.services.telegram import send_message
from app.services.weather import geocode_city

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings():
    s = load_settings()
    return SettingsResponse(
        location_city=s.location.city,
        location_latitude=s.location.latitude,
        location_longitude=s.location.longitude,
        telegram_bot_token_set=bool(s.telegram.bot_token),
        telegram_chat_id=s.telegram.chat_id,
        reminder_time=s.reminder_time,
    )


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

    return SettingsResponse(
        location_city=s.location.city,
        location_latitude=s.location.latitude,
        location_longitude=s.location.longitude,
        telegram_bot_token_set=bool(s.telegram.bot_token),
        telegram_chat_id=s.telegram.chat_id,
        reminder_time=s.reminder_time,
    )


@router.post("/test-telegram")
async def test_telegram():
    s = load_settings()
    if not s.telegram.bot_token or not s.telegram.chat_id:
        raise HTTPException(status_code=400, detail="Telegram not configured")

    success = await send_message(
        s.telegram.bot_token,
        s.telegram.chat_id,
        "Plant Tracker: test message! Your Telegram notifications are working.",
    )
    if not success:
        raise HTTPException(status_code=502, detail="Failed to send Telegram message")
    return {"status": "sent"}
```

- [ ] **Step 4: Add settings router to main app**

In `backend/app/main.py`, add import and include:
```python
from app.routers import plants, settings_router
```
```python
app.include_router(settings_router.router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_settings.py -v`
Expected: All 6 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/settings_router.py backend/app/main.py backend/tests/test_settings.py
git commit -m "feat: add settings API with geocoding and Telegram test"
```

---

## Task 11: Background Job Scheduler

**Files:**
- Create: `backend/app/services/scheduler.py`
- Modify: `backend/app/main.py` (start scheduler in lifespan)

- [ ] **Step 1: Implement scheduler**

`backend/app/services/scheduler.py`:
```python
import logging
from datetime import datetime

import aiosqlite
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import get_db_path
from app.services.claude import adjust_schedules
from app.services.telegram import format_watering_reminder, send_message
from app.services.watering import get_plants_needing_water
from app.services.weather import fetch_weather
from app.settings import load_settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def job_fetch_weather():
    """Daily: fetch weather and cache it."""
    settings = load_settings()
    if not settings.location.latitude:
        logger.warning("No location configured, skipping weather fetch")
        return

    try:
        days = await fetch_weather(
            settings.location.latitude, settings.location.longitude, days=1
        )
    except Exception:
        logger.exception("Weather fetch failed")
        return

    async with aiosqlite.connect(get_db_path()) as db:
        for day in days:
            await db.execute("""
                INSERT OR REPLACE INTO weather_cache
                    (date, temp_high, temp_low, humidity, precipitation_mm)
                VALUES (?, ?, ?, ?, ?)
            """, (
                day["date"], day["temp_high"], day["temp_low"],
                day["humidity"], day["precipitation_mm"],
            ))
        await db.commit()
    logger.info("Weather cache updated: %d days", len(days))


async def job_send_reminders():
    """Daily: send Telegram reminders for plants needing water."""
    settings = load_settings()
    if not settings.telegram.bot_token:
        return

    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        due_plants = await get_plants_needing_water(db)

    message = format_watering_reminder(due_plants)
    if message:
        await send_message(
            settings.telegram.bot_token, settings.telegram.chat_id, message
        )
        logger.info("Sent reminder for %d plants", len(due_plants))


async def job_adjust_schedules():
    """Weekly: use Claude to adjust watering schedules based on weather."""
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")

        # Gather plant data
        cursor = await db.execute("""
            SELECT p.id, p.species, s.interval_days
            FROM plants p
            JOIN watering_schedules s ON p.id = s.plant_id
            WHERE p.species IS NOT NULL
        """)
        plants = [dict(row) for row in await cursor.fetchall()]

        if not plants:
            return

        # Gather recent weather
        cursor = await db.execute("""
            SELECT date, temp_high, temp_low, humidity, precipitation_mm
            FROM weather_cache
            WHERE date >= date('now', '-7 days')
            ORDER BY date
        """)
        weather = [dict(row) for row in await cursor.fetchall()]

        if not weather:
            logger.warning("No weather data for schedule adjustment")
            return

    adjustments = await adjust_schedules(plants, weather)

    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        for adj in adjustments:
            await db.execute("""
                UPDATE watering_schedules
                SET interval_days = ?,
                    last_adjusted = CURRENT_TIMESTAMP,
                    adjustment_reason = ?,
                    next_watering = datetime(
                        (SELECT watered_at FROM watering_logs
                         WHERE plant_id = ? ORDER BY watered_at DESC LIMIT 1),
                        '+' || ? || ' days'
                    )
                WHERE plant_id = ?
            """, (
                adj["interval_days"],
                adj.get("reason", "weather adjustment"),
                adj["plant_id"],
                int(adj["interval_days"]),
                adj["plant_id"],
            ))
        await db.commit()
    logger.info("Adjusted schedules for %d plants", len(adjustments))


def start_scheduler():
    # Weather fetch: daily at 06:00
    scheduler.add_job(
        job_fetch_weather,
        CronTrigger(hour=6, minute=0),
        id="fetch_weather",
        replace_existing=True,
    )

    # Reminders: daily at configured time (default 09:00)
    settings = load_settings()
    hour, minute = (int(x) for x in settings.reminder_time.split(":"))
    scheduler.add_job(
        job_send_reminders,
        CronTrigger(hour=hour, minute=minute),
        id="send_reminders",
        replace_existing=True,
    )

    # Schedule adjustment: weekly on Monday at 07:00
    scheduler.add_job(
        job_adjust_schedules,
        CronTrigger(day_of_week="mon", hour=7, minute=0),
        id="adjust_schedules",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with 3 jobs")


def stop_scheduler():
    scheduler.shutdown(wait=False)
```

- [ ] **Step 2: Wire scheduler into app lifespan**

Update `backend/app/main.py` lifespan:
```python
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield
    stop_scheduler()
```

- [ ] **Step 3: Run all backend tests**

Run: `cd backend && uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/scheduler.py backend/app/main.py
git commit -m "feat: add APScheduler with weather, reminder, and adjustment jobs"
```

---

## Task 12: Photo Serving Endpoint + Static File Serving

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add photo serving and static file mount**

Update `backend/app/main.py` to serve photos and the frontend build:
```python
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import plants, settings_router
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    os.makedirs("./photos", exist_ok=True)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Plant Tracker", lifespan=lifespan)
app.include_router(plants.router)
app.include_router(settings_router.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Serve uploaded photos
app.mount("/photos", StaticFiles(directory="photos"), name="photos")

# Serve frontend build (must be last — catches all unmatched routes)
_frontend_dir = os.environ.get("PLANTS_FRONTEND_DIR", "../frontend/build")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
```

- [ ] **Step 2: Update plants router to return web-accessible photo URL**

In `backend/app/routers/plants.py`, update `add_plant` to store a relative path:

Replace the filepath construction:
```python
    filepath = os.path.join(photo_dir, filename)
```
With:
```python
    filepath = os.path.join(photo_dir, filename)
    # Store relative path for web serving
    web_path = f"/photos/{filename}"
```

And store `web_path` instead of `filepath` in the DB:
```python
    cursor = await db.execute(
        "INSERT INTO plants (name, photo_path) VALUES (?, ?)",
        (name, web_path),
    )
```

Update `_identify_and_update` to receive the actual filesystem path separately for Claude CLI.

- [ ] **Step 3: Run all tests**

Run: `cd backend && uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/main.py backend/app/routers/plants.py
git commit -m "feat: add photo serving and static file mount for frontend"
```

---

## Task 13: Frontend — Global Styles + API Client + Types

**Files:**
- Create: `frontend/src/lib/types.ts`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/app.css`

- [ ] **Step 1: Create TypeScript types**

`frontend/src/lib/types.ts`:
```typescript
export interface PlantIdentification {
    species: string;
    confidence: string;
    care_summary: string;
    light_preference: string;
    base_watering_interval_days: number;
    overwatering_signs: string;
    underwatering_signs: string;
}

export interface Plant {
    id: number;
    name: string;
    species: string | null;
    photo_path: string;
    identification_details: PlantIdentification | null;
    base_watering_interval_days: number | null;
    created_at: string;
    interval_days: number | null;
    next_watering: string | null;
    adjustment_reason: string | null;
}

export interface PlantDetail extends Plant {
    watering_logs: WateringLog[];
}

export interface WateringLog {
    id: number;
    watered_at: string;
    notes: string | null;
}

export interface Settings {
    location_city: string;
    location_latitude: number;
    location_longitude: number;
    telegram_bot_token_set: boolean;
    telegram_chat_id: string;
    reminder_time: string;
}

export interface SettingsUpdate {
    location_city?: string;
    telegram_bot_token?: string;
    telegram_chat_id?: string;
    reminder_time?: string;
}
```

- [ ] **Step 2: Create API client**

`frontend/src/lib/api.ts`:
```typescript
import type { Plant, PlantDetail, Settings, SettingsUpdate } from './types';

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const resp = await fetch(`${BASE}${path}`, {
        headers: { 'Content-Type': 'application/json', ...options?.headers },
        ...options,
    });
    if (!resp.ok) {
        throw new Error(`API error: ${resp.status}`);
    }
    if (resp.status === 204) return undefined as T;
    return resp.json();
}

export async function getPlants(): Promise<Plant[]> {
    return request('/plants');
}

export async function getPlant(id: number): Promise<PlantDetail> {
    return request(`/plants/${id}`);
}

export async function addPlant(name: string, photo: File): Promise<Plant> {
    const form = new FormData();
    form.append('name', name);
    form.append('photo', photo);
    const resp = await fetch(`${BASE}/plants`, { method: 'POST', body: form });
    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    return resp.json();
}

export async function waterPlant(id: number, notes?: string): Promise<void> {
    await request(`/plants/${id}/water`, {
        method: 'POST',
        body: JSON.stringify({ notes: notes || null }),
    });
}

export async function deletePlant(id: number): Promise<void> {
    await request(`/plants/${id}`, { method: 'DELETE' });
}

export async function getSettings(): Promise<Settings> {
    return request('/settings');
}

export async function updateSettings(data: SettingsUpdate): Promise<Settings> {
    return request('/settings', {
        method: 'PUT',
        body: JSON.stringify(data),
    });
}

export async function testTelegram(): Promise<void> {
    await request('/settings/test-telegram', { method: 'POST' });
}
```

- [ ] **Step 3: Create global styles**

`frontend/src/app.css`:
```css
:root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: rgba(255, 255, 255, 0.08);
    --text: #e4e4e7;
    --text-muted: rgba(255, 255, 255, 0.5);
    --green: #4ade80;
    --green-bg: rgba(74, 222, 128, 0.1);
    --blue: #60a5fa;
    --blue-bg: rgba(96, 165, 250, 0.1);
    --yellow: #facc15;
    --yellow-bg: rgba(250, 204, 21, 0.08);
    --red: #ef4444;
    --red-bg: rgba(239, 68, 68, 0.08);
    --radius: 12px;
    --radius-sm: 8px;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100dvh;
    -webkit-font-smoothing: antialiased;
}

button {
    cursor: pointer;
    border: none;
    font: inherit;
}

input {
    font: inherit;
    background: var(--surface);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 0.7rem 1rem;
    width: 100%;
}

input:focus {
    outline: none;
    border-color: var(--green);
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/types.ts frontend/src/lib/api.ts frontend/src/app.css
git commit -m "feat: add frontend types, API client, and global styles"
```

---

## Task 14: Frontend — App Shell + Bottom Navigation

**Files:**
- Create: `frontend/src/routes/+layout.svelte`

- [ ] **Step 1: Create app layout with bottom nav**

`frontend/src/routes/+layout.svelte`:
```svelte
<script lang="ts">
    import '../app.css';
    import { page } from '$app/stores';

    $: path = $page.url.pathname;
</script>

<div class="app">
    <main>
        <slot />
    </main>

    <nav class="bottom-nav">
        <a href="/" class:active={path === '/'}>
            <span class="icon">🏠</span>
            <span class="label">Home</span>
        </a>
        <a href="/add" class:active={path === '/add'}>
            <span class="icon">➕</span>
            <span class="label">Add</span>
        </a>
        <a href="/settings" class:active={path === '/settings'}>
            <span class="icon">⚙️</span>
            <span class="label">Settings</span>
        </a>
    </nav>
</div>

<style>
    .app {
        min-height: 100dvh;
        display: flex;
        flex-direction: column;
        max-width: 480px;
        margin: 0 auto;
    }

    main {
        flex: 1;
        padding: 1rem;
        padding-bottom: calc(4rem + env(safe-area-inset-bottom, 0px));
    }

    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        display: flex;
        justify-content: space-around;
        background: var(--surface);
        border-top: 1px solid var(--border);
        padding: 0.5rem 0;
        padding-bottom: calc(0.5rem + env(safe-area-inset-bottom, 0px));
        z-index: 100;
    }

    .bottom-nav a {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.2rem;
        text-decoration: none;
        color: var(--text-muted);
        font-size: 0.7rem;
        padding: 0.3rem 1rem;
        transition: color 0.15s;
    }

    .bottom-nav a.active {
        color: var(--green);
    }

    .icon {
        font-size: 1.3rem;
    }
</style>
```

- [ ] **Step 2: Verify frontend builds**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/+layout.svelte frontend/src/routes/+layout.ts
git commit -m "feat: add app shell with bottom navigation"
```

---

## Task 15: Frontend — Dashboard Page

**Files:**
- Create: `frontend/src/routes/+page.svelte`

- [ ] **Step 1: Create dashboard page**

`frontend/src/routes/+page.svelte`:
```svelte
<script lang="ts">
    import { onMount } from 'svelte';
    import { getPlants, waterPlant } from '$lib/api';
    import type { Plant } from '$lib/types';

    let plants: Plant[] = [];
    let loading = true;
    let error = '';

    onMount(loadPlants);

    async function loadPlants() {
        try {
            plants = await getPlants();
        } catch (e) {
            error = 'Failed to load plants';
        } finally {
            loading = false;
        }
    }

    function getStatus(plant: Plant): 'overdue' | 'due' | 'upcoming' | 'unscheduled' {
        if (!plant.next_watering) return 'unscheduled';
        const next = new Date(plant.next_watering);
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const nextDay = new Date(next.getFullYear(), next.getMonth(), next.getDate());
        if (nextDay < today) return 'overdue';
        if (nextDay.getTime() === today.getTime()) return 'due';
        return 'upcoming';
    }

    function daysUntil(dateStr: string): string {
        const next = new Date(dateStr);
        const now = new Date();
        const diff = Math.ceil((next.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
        if (diff < 0) return `${Math.abs(diff)} day${Math.abs(diff) !== 1 ? 's' : ''} overdue`;
        if (diff === 0) return 'Due today';
        return `in ${diff} day${diff !== 1 ? 's' : ''}`;
    }

    async function handleWater(plant: Plant) {
        try {
            await waterPlant(plant.id);
            await loadPlants();
        } catch {
            error = 'Failed to log watering';
        }
    }

    $: dueCount = plants.filter(p => {
        const s = getStatus(p);
        return s === 'due' || s === 'overdue';
    }).length;

    $: today = new Date().toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
    });
</script>

<div class="dashboard">
    <header class="header">
        <div class="date">{today}</div>
        {#if dueCount > 0}
            <div class="due-count">{dueCount} plant{dueCount !== 1 ? 's' : ''} need{dueCount === 1 ? 's' : ''} water</div>
        {:else if plants.length > 0}
            <div class="all-good">All plants are happy!</div>
        {/if}
    </header>

    {#if loading}
        <p class="muted">Loading...</p>
    {:else if error}
        <p class="error">{error}</p>
    {:else if plants.length === 0}
        <div class="empty">
            <p>No plants yet.</p>
            <a href="/add" class="add-link">Add your first plant</a>
        </div>
    {:else}
        <div class="plant-list">
            {#each plants as plant}
                {@const status = getStatus(plant)}
                <a href="/plants/{plant.id}" class="plant-card {status}">
                    <img
                        src={plant.photo_path}
                        alt={plant.name}
                        class="plant-photo"
                    />
                    <div class="plant-info">
                        <div class="plant-name">{plant.name}</div>
                        <div class="plant-species">{plant.species || 'Identifying...'}</div>
                        {#if plant.next_watering}
                            <div class="plant-status" class:overdue={status === 'overdue'} class:due={status === 'due'}>
                                {daysUntil(plant.next_watering)}
                            </div>
                        {/if}
                    </div>
                    {#if status === 'due' || status === 'overdue'}
                        <button
                            class="water-btn"
                            on:click|preventDefault|stopPropagation={() => handleWater(plant)}
                        >
                            💧
                        </button>
                    {/if}
                </a>
            {/each}
        </div>
    {/if}
</div>

<style>
    .header {
        margin-bottom: 1.5rem;
    }

    .date {
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
    }

    .due-count {
        font-size: 1.1rem;
        color: var(--green);
        margin-top: 0.3rem;
    }

    .all-good {
        font-size: 1.1rem;
        color: var(--green);
        margin-top: 0.3rem;
    }

    .plant-list {
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
    }

    .plant-card {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        padding: 0.8rem;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        text-decoration: none;
        color: inherit;
        transition: background 0.15s;
    }

    .plant-card:active {
        background: var(--surface);
    }

    .plant-card.overdue {
        background: var(--red-bg);
        border-color: rgba(239, 68, 68, 0.2);
    }

    .plant-card.due {
        background: var(--yellow-bg);
        border-color: rgba(250, 204, 21, 0.2);
    }

    .plant-photo {
        width: 48px;
        height: 48px;
        border-radius: var(--radius-sm);
        object-fit: cover;
    }

    .plant-info {
        flex: 1;
        min-width: 0;
    }

    .plant-name {
        font-weight: 600;
        font-size: 0.9rem;
    }

    .plant-species {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    .plant-status {
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-top: 0.2rem;
    }

    .plant-status.overdue {
        color: var(--red);
    }

    .plant-status.due {
        color: var(--yellow);
    }

    .water-btn {
        background: var(--green-bg);
        border: 1px solid rgba(74, 222, 128, 0.3);
        border-radius: var(--radius-sm);
        padding: 0.5rem 0.7rem;
        font-size: 1.2rem;
    }

    .empty {
        text-align: center;
        padding: 3rem 1rem;
        color: var(--text-muted);
    }

    .add-link {
        display: inline-block;
        margin-top: 1rem;
        color: var(--green);
        text-decoration: none;
        padding: 0.6rem 1.2rem;
        border: 1px solid rgba(74, 222, 128, 0.3);
        border-radius: var(--radius-sm);
    }

    .muted { color: var(--text-muted); }
    .error { color: var(--red); }
</style>
```

- [ ] **Step 2: Verify frontend builds**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/+page.svelte
git commit -m "feat: add dashboard page with plant list and quick watering"
```

---

## Task 16: Frontend — Add Plant Page

**Files:**
- Create: `frontend/src/routes/add/+page.svelte`

- [ ] **Step 1: Create add plant page**

`frontend/src/routes/add/+page.svelte`:
```svelte
<script lang="ts">
    import { goto } from '$app/navigation';
    import { addPlant } from '$lib/api';

    let name = '';
    let photo: File | null = null;
    let preview = '';
    let submitting = false;
    let error = '';

    function handleFileChange(e: Event) {
        const input = e.target as HTMLInputElement;
        const file = input.files?.[0];
        if (file) {
            photo = file;
            preview = URL.createObjectURL(file);
        }
    }

    async function handleSubmit() {
        if (!name.trim() || !photo) return;
        submitting = true;
        error = '';
        try {
            const plant = await addPlant(name.trim(), photo);
            goto(`/plants/${plant.id}`);
        } catch {
            error = 'Failed to add plant. Please try again.';
            submitting = false;
        }
    }
</script>

<div class="add-plant">
    <h2>Add a New Plant</h2>

    <label class="photo-upload" class:has-photo={!!preview}>
        {#if preview}
            <img src={preview} alt="Preview" class="preview" />
        {:else}
            <div class="upload-prompt">
                <span class="camera">📷</span>
                <span>Tap to take or upload photo</span>
            </div>
        {/if}
        <input
            type="file"
            accept="image/*"
            capture="environment"
            on:change={handleFileChange}
            hidden
        />
    </label>

    <div class="field">
        <label for="name">Name your plant</label>
        <input
            id="name"
            bind:value={name}
            placeholder='e.g. "Kitchen Basil"'
        />
    </div>

    {#if error}
        <p class="error">{error}</p>
    {/if}

    <button
        class="submit"
        on:click={handleSubmit}
        disabled={!name.trim() || !photo || submitting}
    >
        {submitting ? 'Adding...' : 'Add & Identify Plant'}
    </button>

    <div class="info">
        <p class="info-title">After adding, Claude will:</p>
        <ol>
            <li>Identify the plant species</li>
            <li>Provide care information</li>
            <li>Set a watering schedule based on your weather</li>
        </ol>
    </div>
</div>

<style>
    .add-plant {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    h2 {
        font-size: 1.2rem;
    }

    .photo-upload {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 200px;
        border: 2px dashed var(--border);
        border-radius: var(--radius);
        cursor: pointer;
        overflow: hidden;
    }

    .photo-upload.has-photo {
        border-style: solid;
    }

    .upload-prompt {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
        color: var(--text-muted);
        font-size: 0.85rem;
    }

    .camera {
        font-size: 2rem;
    }

    .preview {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .field label {
        display: block;
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-bottom: 0.3rem;
    }

    .submit {
        width: 100%;
        padding: 0.8rem;
        background: var(--green-bg);
        color: var(--green);
        border: 1px solid rgba(74, 222, 128, 0.3);
        border-radius: var(--radius-sm);
        font-weight: 600;
    }

    .submit:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

    .info {
        padding: 0.8rem;
        background: var(--blue-bg);
        border: 1px solid rgba(96, 165, 250, 0.15);
        border-radius: var(--radius-sm);
        font-size: 0.8rem;
    }

    .info-title {
        color: var(--text-muted);
        margin-bottom: 0.4rem;
    }

    .info ol {
        padding-left: 1.2rem;
        color: var(--text-muted);
        line-height: 1.8;
    }

    .error { color: var(--red); font-size: 0.85rem; }
</style>
```

- [ ] **Step 2: Verify frontend builds**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/add/+page.svelte
git commit -m "feat: add plant creation page with photo upload"
```

---

## Task 17: Frontend — Plant Detail Page

**Files:**
- Create: `frontend/src/routes/plants/[id]/+page.svelte`

- [ ] **Step 1: Create plant detail page**

`frontend/src/routes/plants/[id]/+page.svelte`:
```svelte
<script lang="ts">
    import { page } from '$app/stores';
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { getPlant, waterPlant, deletePlant } from '$lib/api';
    import type { PlantDetail } from '$lib/types';

    let plant: PlantDetail | null = null;
    let loading = true;
    let error = '';

    $: id = Number($page.params.id);

    onMount(loadPlant);

    async function loadPlant() {
        try {
            plant = await getPlant(id);
        } catch {
            error = 'Plant not found';
        } finally {
            loading = false;
        }
    }

    async function handleWater() {
        if (!plant) return;
        try {
            await waterPlant(plant.id);
            await loadPlant();
        } catch {
            error = 'Failed to log watering';
        }
    }

    async function handleDelete() {
        if (!plant || !confirm(`Delete ${plant.name}?`)) return;
        try {
            await deletePlant(plant.id);
            goto('/');
        } catch {
            error = 'Failed to delete plant';
        }
    }

    function formatDate(dateStr: string): string {
        return new Date(dateStr).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
        });
    }

    function daysUntil(dateStr: string): string {
        const next = new Date(dateStr);
        const now = new Date();
        const diff = Math.ceil((next.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
        if (diff < 0) return `${Math.abs(diff)}d overdue`;
        if (diff === 0) return 'Today';
        return `in ${diff}d`;
    }
</script>

{#if loading}
    <p class="muted">Loading...</p>
{:else if error}
    <p class="error">{error}</p>
{:else if plant}
    <div class="detail">
        <img src={plant.photo_path} alt={plant.name} class="hero" />

        <div class="info-section">
            <h2>{plant.name}</h2>
            <p class="species">
                {plant.species || 'Identifying...'}
                {#if plant.created_at}
                    · Added {formatDate(plant.created_at)}
                {/if}
            </p>
        </div>

        {#if plant.interval_days && plant.next_watering}
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{plant.interval_days}d</div>
                    <div class="stat-label">Interval</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{daysUntil(plant.next_watering)}</div>
                    <div class="stat-label">Next watering</div>
                </div>
            </div>
        {/if}

        <button class="water-btn" on:click={handleWater}>
            💧 Mark as Watered
        </button>

        {#if plant.adjustment_reason}
            <div class="adjustment">
                <strong>Schedule note:</strong> {plant.adjustment_reason}
            </div>
        {/if}

        {#if plant.identification_details}
            <div class="care-section">
                <h3>Care Info</h3>
                <p>{plant.identification_details.care_summary}</p>
                <div class="care-detail">
                    <span class="care-label">Light:</span> {plant.identification_details.light_preference}
                </div>
            </div>
        {/if}

        {#if plant.watering_logs.length > 0}
            <div class="history-section">
                <h3>Watering History</h3>
                {#each plant.watering_logs.slice(0, 10) as log}
                    <div class="log-entry">
                        <span>💧 {formatDate(log.watered_at)}</span>
                        {#if log.notes}
                            <span class="log-notes">{log.notes}</span>
                        {/if}
                    </div>
                {/each}
            </div>
        {/if}

        <button class="delete-btn" on:click={handleDelete}>
            Delete Plant
        </button>
    </div>
{/if}

<style>
    .hero {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: var(--radius);
    }

    .info-section {
        margin-top: 1rem;
    }

    h2 { font-size: 1.3rem; }

    .species {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-top: 0.2rem;
    }

    .stats {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.6rem;
        margin-top: 1rem;
    }

    .stat {
        padding: 0.6rem;
        background: var(--surface);
        border-radius: var(--radius-sm);
        text-align: center;
    }

    .stat-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--green);
    }

    .stat-label {
        font-size: 0.7rem;
        color: var(--text-muted);
    }

    .water-btn {
        width: 100%;
        padding: 0.8rem;
        margin-top: 1rem;
        background: var(--green-bg);
        color: var(--green);
        border: 1px solid rgba(74, 222, 128, 0.3);
        border-radius: var(--radius-sm);
        font-weight: 600;
        font-size: 1rem;
    }

    .adjustment {
        margin-top: 1rem;
        padding: 0.6rem;
        background: var(--yellow-bg);
        border: 1px solid rgba(250, 204, 21, 0.15);
        border-radius: var(--radius-sm);
        font-size: 0.8rem;
    }

    .care-section, .history-section {
        margin-top: 1.5rem;
    }

    h3 {
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }

    .care-section p {
        font-size: 0.85rem;
        color: var(--text-muted);
        line-height: 1.5;
    }

    .care-detail {
        margin-top: 0.4rem;
        font-size: 0.8rem;
    }

    .care-label {
        color: var(--text-muted);
    }

    .log-entry {
        display: flex;
        justify-content: space-between;
        padding: 0.4rem 0;
        border-bottom: 1px solid var(--border);
        font-size: 0.8rem;
    }

    .log-notes {
        color: var(--text-muted);
        font-size: 0.75rem;
    }

    .delete-btn {
        width: 100%;
        padding: 0.7rem;
        margin-top: 2rem;
        background: transparent;
        color: var(--red);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-radius: var(--radius-sm);
        font-size: 0.85rem;
    }

    .muted { color: var(--text-muted); }
    .error { color: var(--red); }
</style>
```

- [ ] **Step 2: Verify frontend builds**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/plants/
git commit -m "feat: add plant detail page with watering history"
```

---

## Task 18: Frontend — Settings Page

**Files:**
- Create: `frontend/src/routes/settings/+page.svelte`

- [ ] **Step 1: Create settings page**

`frontend/src/routes/settings/+page.svelte`:
```svelte
<script lang="ts">
    import { onMount } from 'svelte';
    import { getSettings, updateSettings, testTelegram } from '$lib/api';
    import type { Settings } from '$lib/types';

    let city = '';
    let botToken = '';
    let chatId = '';
    let reminderTime = '09:00';
    let tokenAlreadySet = false;

    let saving = false;
    let testing = false;
    let message = '';
    let messageType: 'success' | 'error' = 'success';

    onMount(async () => {
        try {
            const s = await getSettings();
            city = s.location_city;
            chatId = s.telegram_chat_id;
            reminderTime = s.reminder_time;
            tokenAlreadySet = s.telegram_bot_token_set;
        } catch {
            showMessage('Failed to load settings', 'error');
        }
    });

    function showMessage(msg: string, type: 'success' | 'error') {
        message = msg;
        messageType = type;
        setTimeout(() => { message = ''; }, 3000);
    }

    async function handleSave() {
        saving = true;
        try {
            const update: Record<string, string> = {
                location_city: city,
                telegram_chat_id: chatId,
                reminder_time: reminderTime,
            };
            if (botToken) {
                update.telegram_bot_token = botToken;
            }
            await updateSettings(update);
            tokenAlreadySet = tokenAlreadySet || !!botToken;
            botToken = '';
            showMessage('Settings saved', 'success');
        } catch {
            showMessage('Failed to save settings', 'error');
        } finally {
            saving = false;
        }
    }

    async function handleTestTelegram() {
        testing = true;
        try {
            await testTelegram();
            showMessage('Test message sent!', 'success');
        } catch {
            showMessage('Failed to send test message', 'error');
        } finally {
            testing = false;
        }
    }
</script>

<div class="settings">
    <h2>Settings</h2>

    <div class="field">
        <label for="city">Location (for weather)</label>
        <input id="city" bind:value={city} placeholder="e.g. Amsterdam" />
    </div>

    <div class="field">
        <label for="token">
            Telegram Bot Token
            {#if tokenAlreadySet}
                <span class="badge">configured</span>
            {/if}
        </label>
        <input
            id="token"
            bind:value={botToken}
            placeholder={tokenAlreadySet ? 'Leave blank to keep current' : 'Paste bot token'}
            type="password"
        />
    </div>

    <div class="field">
        <label for="chat">Telegram Chat ID</label>
        <input id="chat" bind:value={chatId} placeholder="Your chat ID" />
    </div>

    <div class="field">
        <label for="time">Reminder Time</label>
        <input id="time" type="time" bind:value={reminderTime} />
    </div>

    {#if message}
        <p class="{messageType}">{message}</p>
    {/if}

    <button class="save-btn" on:click={handleSave} disabled={saving}>
        {saving ? 'Saving...' : 'Save Settings'}
    </button>

    <button
        class="test-btn"
        on:click={handleTestTelegram}
        disabled={testing || !tokenAlreadySet}
    >
        {testing ? 'Sending...' : 'Send Test Telegram Message'}
    </button>
</div>

<style>
    .settings {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    h2 { font-size: 1.2rem; }

    .field label {
        display: block;
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-bottom: 0.3rem;
    }

    .badge {
        display: inline-block;
        padding: 0.1rem 0.4rem;
        background: var(--green-bg);
        color: var(--green);
        border-radius: 4px;
        font-size: 0.65rem;
    }

    .save-btn {
        width: 100%;
        padding: 0.7rem;
        background: var(--green-bg);
        color: var(--green);
        border: 1px solid rgba(74, 222, 128, 0.3);
        border-radius: var(--radius-sm);
        font-weight: 600;
    }

    .test-btn {
        width: 100%;
        padding: 0.7rem;
        background: var(--blue-bg);
        color: var(--blue);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: var(--radius-sm);
    }

    .test-btn:disabled, .save-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

    .success { color: var(--green); font-size: 0.85rem; }
    .error { color: var(--red); font-size: 0.85rem; }
</style>
```

- [ ] **Step 2: Verify frontend builds**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/settings/
git commit -m "feat: add settings page with Telegram test"
```

---

## Task 19: PWA Manifest + Service Worker

**Files:**
- Create: `frontend/static/manifest.json`
- Modify: `frontend/src/app.html`

- [ ] **Step 1: Create PWA manifest**

`frontend/static/manifest.json`:
```json
{
    "name": "Plant Tracker",
    "short_name": "Plants",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0f1117",
    "theme_color": "#4ade80",
    "icons": [
        {
            "src": "/icon-192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/icon-512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ]
}
```

- [ ] **Step 2: Update app.html with PWA meta tags**

`frontend/src/app.html`:
```html
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        <meta name="theme-color" content="#4ade80" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <link rel="manifest" href="/manifest.json" />
        <link rel="icon" href="/icon-192.png" />
        <link rel="apple-touch-icon" href="/icon-192.png" />
        <title>Plant Tracker</title>
        %sveltekit.head%
    </head>
    <body data-sveltekit-preload-data="hover">
        <div style="display: contents">%sveltekit.body%</div>
    </body>
</html>
```

- [ ] **Step 3: Generate placeholder PWA icons**

Run: `cd frontend/static && python3 -c "
from PIL import Image, ImageDraw
for size in [192, 512]:
    img = Image.new('RGB', (size, size), '#0f1117')
    d = ImageDraw.Draw(img)
    d.ellipse([size//4, size//4, 3*size//4, 3*size//4], fill='#4ade80')
    img.save(f'icon-{size}.png')
" 2>/dev/null || echo "Pillow not installed — create icon-192.png and icon-512.png manually (any PNG will do)"`

If Pillow is not available, create simple placeholder PNGs manually. Any 192x192 and 512x512 PNG will work.

- [ ] **Step 4: Verify frontend builds**

Run: `cd frontend && npm run build`
Expected: Build succeeds, `manifest.json` in build output

- [ ] **Step 5: Commit**

```bash
git add frontend/static/manifest.json frontend/src/app.html frontend/static/icon-*.png
git commit -m "feat: add PWA manifest and meta tags"
```

---

## Task 20: Integration Test + Final Wiring

**Files:**
- Modify: `backend/app/main.py` (finalize)

- [ ] **Step 1: Run full backend test suite**

Run: `cd backend && uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 2: Build frontend and test full stack locally**

Run: `cd frontend && npm run build`
Then: `cd backend && PLANTS_DB_PATH=./test_run.db uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`

Open `http://localhost:8000` in a mobile-width browser. Verify:
- Dashboard renders (empty state)
- Settings page loads
- Add plant page opens with camera/upload prompt
- Bottom navigation works

Clean up: `rm backend/test_run.db`

- [ ] **Step 3: Commit any final fixes**

```bash
git add -A
git commit -m "chore: integration verification and final adjustments"
```

- [ ] **Step 4: Final commit — tag v0.1.0**

```bash
git tag v0.1.0
```
