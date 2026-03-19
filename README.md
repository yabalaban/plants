# Plant Tracker

Personal plant care PWA with AI-powered identification and weather-adaptive watering schedules.

Upload a photo of your plant, Claude identifies the species and sets up a watering schedule that adjusts based on your local weather. Get daily reminders via Telegram.

## Stack

- **Backend:** FastAPI, SQLite, APScheduler
- **Frontend:** SvelteKit (static PWA)
- **AI:** Claude CLI (plant identification + schedule adjustment)
- **Weather:** Open-Meteo (free, no API key)
- **Notifications:** Telegram Bot API

## Prerequisites

- [mise](https://mise.jdx.dev/) installed
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated
- A Telegram bot (create via [@BotFather](https://t.me/BotFather))

## Setup

```bash
# Install tool versions (Python 3.12, Node 22, uv)
mise install

# Install backend dependencies
cd backend && uv sync && cd ..

# Build frontend
cd frontend && npm install && npm run build && cd ..
```

## Run

```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://<your-ip>:8000` on your phone.

## Development

Run backend and frontend dev servers separately:

```bash
# Terminal 1: backend
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Terminal 2: frontend (with proxy to backend)
cd frontend && npm run dev
```

Vite proxies `/api` and `/photos` to the backend automatically.

## Configuration

On first run, go to Settings in the app and configure:

1. **Location** - your city (for weather-based schedule adjustments)
2. **Telegram Bot Token** - from @BotFather
3. **Telegram Chat ID** - your personal chat ID
4. **Reminder Time** - when to receive daily watering reminders

## Background Jobs

The server runs three scheduled jobs:

| Job | Schedule | Description |
|-----|----------|-------------|
| Weather fetch | Daily 06:00 | Fetches local weather from Open-Meteo |
| Watering reminders | Daily (configurable) | Sends Telegram message for due/overdue plants |
| Schedule adjustment | Weekly (Monday 07:00) | Claude re-evaluates watering intervals based on weather |

## Tests

```bash
cd backend && uv run pytest -v
```

## Deploy on Raspberry Pi

```bash
git clone <repo-url> plants && cd plants
mise install
cd backend && uv sync && cd ..
cd frontend && npm install && npm run build && cd ..

# Run (or set up as a systemd service)
cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Access via VPN at `http://<rpi-ip>:8000`.
