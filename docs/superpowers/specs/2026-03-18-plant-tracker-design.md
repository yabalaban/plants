# Plant Life Tracker — Design Spec

Personal mobile-first PWA for tracking houseplants, identifying them via Claude CLI, and maintaining weather-adaptive watering schedules with Telegram reminders.

## Context

- **User:** Single user, personal tool
- **Hosting:** Raspberry Pi, accessed via VPN (plain HTTP, no reverse proxy)
- **Scale:** Under 10 plants

## Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | FastAPI (Python) | Lightweight on RPi, async, good subprocess support |
| Frontend | SvelteKit (compiled to static files) | Smallest JS bundle, native PWA support, mobile-first |
| Database | SQLite | Zero-config, built into Python, perfect for single-user |
| LLM | Claude CLI (`claude -p`) | No SDK dependency, CLI handles auth, invoked as subprocess |
| Weather | Open-Meteo API | Free, no API key required |
| Notifications | Telegram Bot API | Works over plain HTTP, reliable push to phone |
| Scheduler | APScheduler | Runs inside FastAPI process for background jobs |

## Architecture

Single FastAPI process on the Raspberry Pi that:
- Serves the compiled SvelteKit static files (the PWA)
- Exposes REST API endpoints for the frontend
- Runs background jobs (weather fetch, reminders, schedule adjustment)
- Stores photos on the filesystem, metadata in SQLite
- Invokes `claude` CLI as a subprocess for plant identification and schedule adjustments

```
Phone (PWA)  ──HTTP over VPN──►  Raspberry Pi
                                  ├── FastAPI server
                                  │    ├── REST API endpoints
                                  │    ├── Static file serving (Svelte build)
                                  │    └── APScheduler (background jobs)
                                  ├── SQLite database
                                  ├── Photo storage (filesystem)
                                  └── Claude CLI (subprocess calls)
                                       ├── Open-Meteo (weather)
                                       └── Telegram Bot API (notifications)
```

## Data Model

### `plants`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| name | TEXT | User-given name (e.g., "Living Room Monstera") |
| species | TEXT, nullable | Identified by Claude, null until identification completes |
| photo_path | TEXT | Filesystem path to uploaded photo |
| identification_details | TEXT (JSON) | Claude's full identification response (care tips, light preference, etc.) |
| base_watering_interval_days | INTEGER | Claude-recommended default interval |
| created_at | TIMESTAMP | When the plant was added |

### `watering_logs`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| plant_id | INTEGER FK | References `plants.id` (CASCADE DELETE) |
| watered_at | TIMESTAMP | When the user logged watering |
| notes | TEXT, nullable | Optional user note |

### `watering_schedules`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| plant_id | INTEGER FK | References `plants.id` (one active schedule per plant, CASCADE DELETE) |
| interval_days | REAL | Current weather-adjusted watering interval |
| next_watering | TIMESTAMP | Next expected watering date |
| last_adjusted | TIMESTAMP | When the schedule was last modified |
| adjustment_reason | TEXT | Why it was adjusted (e.g., "hot weather", "rainy week") |

### `weather_cache`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| date | DATE | Weather date |
| temp_high | REAL | Daily high temperature (°C) |
| temp_low | REAL | Daily low temperature (°C) |
| humidity | REAL | Average humidity (%) |
| precipitation_mm | REAL | Total precipitation (mm) |
| fetched_at | TIMESTAMP | When the data was fetched |

## Claude CLI Integration

Two distinct invocations, both via `claude -p` (pipe mode) as subprocess calls:

### Plant Identification (on photo upload)

Triggered when a user adds a new plant with a photo. The backend invokes:

```
claude -p "Identify this plant. Return JSON with: species (common + Latin name), confidence level, brief care summary, light preference, base watering interval in days for indoor conditions, signs of overwatering and underwatering." --image <photo_path>
```

The JSON response populates `plants.species`, `plants.identification_details`, `plants.base_watering_interval_days`, and creates the initial `watering_schedules` row.

### Schedule Adjustment (weekly cron)

Triggered by the weekly background job. The backend constructs a prompt containing all plants' current schedules, the past week's weather data from `weather_cache`, and recent watering history, then invokes:

```
claude -p "<constructed prompt with plant + weather + history context>"
```

The response updates `watering_schedules.interval_days`, `next_watering`, and `adjustment_reason` for each plant.

## Background Jobs

| Job | Schedule | Action |
|-----|----------|--------|
| Weather fetch | Daily @ 06:00 | GET Open-Meteo API → insert into `weather_cache` |
| Watering reminders | Daily @ user-configured time | Check `next_watering` for all plants → send Telegram message for due/overdue plants |
| Schedule adjustment | Weekly (Monday) | Batch Claude CLI call to re-evaluate all watering intervals based on weather trends |

## UI Screens (PWA)

Mobile-first layout with bottom tab navigation: Home, Add, Settings.

### 1. Dashboard (Home)

- Today's date and count of plants needing water
- Plant list sorted by urgency: overdue (red) → due today (yellow) → upcoming (neutral)
- Each plant card shows: photo thumbnail, name, status, quick "Water" button for due plants
- Weather summary footer (current conditions, whether schedules were adjusted)

### 2. Add Plant

- Photo upload area (camera capture or gallery pick via mobile browser)
- Text input for plant name
- "Add & Identify" button triggers upload + Claude CLI identification
- Info box explaining what happens after adding

### 3. Plant Detail

- Hero photo of the plant
- Species name and date added
- Current watering interval and next watering date
- "Mark as Watered" button → creates `watering_logs` entry, updates `next_watering`
- Recent watering history list
- Schedule adjustment notes (why the interval was changed)

### 4. Settings

- **Location:** City input for weather (configured once)
- **Telegram Bot Token:** For sending reminders
- **Telegram Chat ID:** Your personal chat ID
- **Reminder Time:** What time of day to send Telegram notifications
- Test button to verify Telegram setup

No Anthropic API key field — Claude CLI manages its own authentication.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/plants` | List all plants with current schedule info |
| POST | `/api/plants` | Add plant (multipart: photo + name). Triggers async identification |
| GET | `/api/plants/{id}` | Plant detail with watering history |
| POST | `/api/plants/{id}/water` | Log a watering event |
| DELETE | `/api/plants/{id}` | Remove a plant |
| GET | `/api/settings` | Get current settings |
| PUT | `/api/settings` | Update settings (location, Telegram config, reminder time) |
| POST | `/api/settings/test-telegram` | Send a test Telegram message |

## Configuration

Settings stored in a `settings.json` file on the filesystem (not in SQLite — simpler for a single-user app):

```json
{
  "location": { "city": "Amsterdam", "latitude": 52.37, "longitude": 4.89 },
  "telegram": { "bot_token": "...", "chat_id": "..." },
  "reminder_time": "09:00",
  "photo_dir": "./photos"
}
```

Latitude/longitude are resolved from the city name on save using Open-Meteo's geocoding API (`geocoding-api.open-meteo.com`). Reminder time uses the Raspberry Pi's system timezone.

## Deployment

Single-process deployment on Raspberry Pi:

1. Clone repo
2. Install Python dependencies (`pip install fastapi uvicorn apscheduler httpx python-telegram-bot aiosqlite`)
3. Build SvelteKit frontend (`npm run build` → static files)
4. Run: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
5. Access from phone via VPN at `http://<rpi-ip>:8000`

Prerequisites: Claude CLI installed and authenticated on the RPi.

## Cost Estimate

- **Claude CLI:** ~1 vision call per plant added (rare) + ~1 text call per week (schedule adjustment). Well under $1/month for <10 plants.
- **Open-Meteo:** Free, no limits for personal use.
- **Telegram Bot API:** Free.

## Error Handling

- **Claude CLI fails:** Retry once. If still failing, log the error and skip (plant stays unidentified / schedule unchanged). User sees status in the app.
- **Weather fetch fails:** Use cached data. If no cache, skip schedule adjustment for the week.
- **Telegram fails:** Log error. User sees missed reminders on the dashboard when they open the app.

## Testing Strategy

- **Backend:** Unit tests for schedule calculation logic, integration tests for API endpoints using test SQLite DB.
- **Claude CLI:** Mock subprocess calls in tests with fixture responses.
- **Frontend:** Component tests for key interactions (add plant, log watering).
