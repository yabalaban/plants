# Plant Tracker

Personal plant care PWA with AI-powered identification and weather-adaptive watering schedules.

Upload a photo of your plant, Claude identifies the species and sets up a watering schedule that adjusts based on your local weather. Get daily reminders via Telegram (delivered by Rick Sanchez).

## Stack

- **Backend:** FastAPI, SQLite, APScheduler
- **Frontend:** SvelteKit (static PWA)
- **AI:** Claude CLI with structured output (`--json-schema`)
- **Weather:** Open-Meteo (free, no API key) — 7 days history + 3 day forecast
- **Notifications:** Telegram Bot API (Rick and Morty themed)

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

1. **Location** — your city (for weather-based schedule adjustments)
2. **Telegram Bot Token** — from @BotFather
3. **Telegram Chat ID** — your personal chat ID
4. **Reminder Time** — when to receive daily watering reminders

When adding a plant, choose **Indoor** or **Balcony** — this affects how temperature data is factored into watering adjustments. You can change the location and name anytime from the plant detail page.

## Background Jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| Weather fetch | Daily 06:00 | Fetches 7 days history + 3 day forecast from Open-Meteo |
| Watering reminders | Daily (configurable) | Sends Telegram message for due/overdue plants |
| Schedule adjustment | Every 3 days at 07:00 | Claude adjusts watering intervals based on weather + plant location |

Schedule adjustment also runs immediately after a new plant is identified, so the first watering interval is weather-aware from the start.

## Debug

Settings → Debug shows:

- **Claude Logs** — every Claude CLI call with prompt, response, duration, and errors
- **Weather Cache** — cached weather data with forecast days marked

Manual triggers are available via the debug API:

```bash
curl -X POST http://<host>:5757/api/debug/weather/fetch      # fetch weather now
curl -X POST http://<host>:5757/api/debug/reminders/send      # send reminder now
curl -X POST http://<host>:5757/api/debug/reminders/preview   # send preview with fake data
```

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

### Build & Deploy

```bash
git clone <repo-url> plants && cd plants
podman build -t plant-tracker:latest .
./deploy.sh
```

The app runs on host port **5757** (container port 8472), accessible at `http://<rpi-ip>:5757`.

### Auto-Start on Boot (systemd)

```bash
# Generate systemd unit from running container
mkdir -p ~/.config/systemd/user
podman generate systemd --name plant-tracker --new \
  > ~/.config/systemd/user/plant-tracker.service

# Enable auto-start
systemctl --user daemon-reload
systemctl --user enable plant-tracker

# Allow services to run without login session
loginctl enable-linger $USER
```

After this, the container starts automatically on boot. To manage via systemd:

```bash
systemctl --user status plant-tracker     # check status
systemctl --user restart plant-tracker    # restart
systemctl --user stop plant-tracker       # stop
journalctl --user -u plant-tracker -f     # view logs
```

Note: `deploy.sh` manages the container directly via Podman. After running `deploy.sh`, the container is Podman-managed (not systemd). On the next reboot, systemd takes over. To keep systemd in control, use `systemctl --user restart plant-tracker` instead of `deploy.sh`.

### Rebuild After Updates

```bash
cd ~/plants && git pull
podman build -t plant-tracker:latest .
./deploy.sh
```

### Management (Podman direct)

```bash
podman logs -f plant-tracker              # tail logs
podman healthcheck run plant-tracker      # check health
podman stop plant-tracker                 # stop
podman restart plant-tracker              # restart
```

### Security

The container runs with multiple hardening layers:

- **Rootless Podman** — no root access on host, even if container is compromised
- **Subordinate UID namespace** — container UID maps to unprivileged host UID, not the real user
- **`--network pasta:--ipv4-only`** — prevents IPv6 accept-then-reset that breaks Safari/Happy Eyeballs
- **Read-only filesystem** — container rootfs is immutable (`/tmp` is tmpfs)
- **No capabilities** — all Linux capabilities dropped
- **No privilege escalation** — setuid/setgid blocked
- **Secrets isolation** — Telegram token stored encrypted, injected at runtime via `/run/secrets/`
- **Claude CLI read-only** — host `~/.claude` and `~/.claude.json` mounted read-only

### Data Layout

```
~/plant-data/
├── db/plants.db         # SQLite database
├── photos/              # Uploaded plant photos
└── config/settings.json # Non-secret config (city, reminder time)
```

All data persists across container rebuilds. Back up `~/plant-data/` to preserve everything.
