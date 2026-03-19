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

| Job | Schedule | Description |
|-----|----------|-------------|
| Weather fetch | Daily 06:00 | Fetches local weather from Open-Meteo |
| Watering reminders | Daily (configurable) | Sends Telegram message for due/overdue plants |
| Schedule adjustment | Weekly (Monday 07:00) | Claude re-evaluates watering intervals based on weather |

## Tests

```bash
cd backend && uv run pytest -v
```

---

## Container Deployment (Raspberry Pi)

The recommended way to run on a Raspberry Pi. Uses Podman (rootless) with full security hardening.

### Prerequisites (on RPi)

- [Podman](https://podman.io/) installed (`sudo apt install podman`)
- [mise](https://mise.jdx.dev/) installed
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated

### One-Time Setup

```bash
# Create data directory
mkdir -p ~/plant-data/{db,photos,config}

# Store Telegram secrets (encrypted by Podman)
echo "YOUR_BOT_TOKEN" | podman secret create telegram_bot_token -
echo "YOUR_CHAT_ID"   | podman secret create telegram_chat_id -
```

To find your Telegram chat ID: message your bot, then:
```bash
curl -s https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates | python3 -m json.tool
```

### Build

```bash
git clone <repo-url> plants && cd plants
podman build -t plant-tracker:latest .
```

### Deploy

```bash
./deploy.sh
```

The app runs on port **8472**, accessible via VPN at `http://<rpi-ip>:8472`.

### Management

```bash
podman logs -f plant-tracker       # tail logs
podman healthcheck run plant-tracker  # check health
podman stop plant-tracker           # stop
podman start plant-tracker          # start
podman restart plant-tracker        # restart after code changes
```

### Auto-Start on Boot

```bash
mkdir -p ~/.config/systemd/user
podman generate systemd --name plant-tracker --new \
  > ~/.config/systemd/user/plant-tracker.service
systemctl --user enable plant-tracker
loginctl enable-linger $USER
```

### Rebuild After Updates

```bash
cd ~/plants && git pull
podman build -t plant-tracker:latest .
./deploy.sh
```

### Security

The container runs with multiple hardening layers:

- **Rootless Podman** — no root access on host, even if container is compromised
- **Non-root user** — app runs as uid 1000 inside the container
- **Read-only filesystem** — container rootfs is immutable (`/tmp` is tmpfs)
- **No capabilities** — all Linux capabilities dropped
- **No privilege escalation** — setuid/setgid blocked
- **Secrets isolation** — Telegram token stored encrypted, injected at runtime via `/run/secrets/`, not visible in `podman inspect` or environment
- **Claude CLI read-only** — mounted from host, container cannot modify auth

### Data Layout

```
~/plant-data/
├── db/plants.db         # SQLite database
├── photos/              # Uploaded plant photos
└── config/settings.json # Non-secret config (city, reminder time)
```

All data persists across container rebuilds. Back up `~/plant-data/` to preserve everything.
