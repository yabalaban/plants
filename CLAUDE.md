# Plant Tracker - Development Guide

## Project Overview

Personal plant care PWA. FastAPI backend + SvelteKit frontend + SQLite. Deployed on Raspberry Pi in a rootless Podman container, accessed via VPN (plain HTTP). Single user, no auth.

## Tooling

- **Python deps**: always use `uv` (never pip/venv directly)
- **Tool versions**: managed by `mise` (Python 3.12, Node 22, uv)
- **If uv is missing**: install via `mise install`
- **Container runtime**: Podman (rootless), NOT Docker

## Architecture

```
backend/app/
├── main.py              # FastAPI app, lifespan, static serving, SPA fallback
├── database.py          # SQLite init + async connection (aiosqlite) + migrations
├── models.py            # Pydantic request/response models
├── settings.py          # settings.json read/write + Podman secrets (/run/secrets/)
├── routers/
│   ├── plants.py        # CRUD + photo upload + background identification + PATCH
│   ├── settings_router.py  # Settings API + Telegram test
│   └── debug.py         # Debug API: weather cache, Claude logs, trigger endpoints
└── services/
    ├── claude.py         # Claude CLI wrapper: --json-schema structured output, call logging
    ├── weather.py        # Open-Meteo geocoding + forecast (7 past + 3 forecast days)
    ├── telegram.py       # Telegram Bot API: Rick and Morty themed reminders
    ├── scheduler.py      # APScheduler: weather fetch, reminders, schedule adjustment
    └── watering.py       # Due/overdue calculation

Deployment files:
├── Containerfile         # Multi-stage: Node builds frontend, Python slim runtime
├── .containerignore      # Keeps image lean (~150MB)
├── deploy.sh            # One-command deploy with security hardening
```

Frontend is SvelteKit compiled to static files, served by FastAPI's catch-all route.

## Running Locally (Dev)

```bash
# Two terminals
cd backend && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev   # Vite proxies /api and /photos to :8000
```

## Tests

```bash
cd backend && uv run pytest -v
```

## Container Deployment (Production)

### Build and deploy

```bash
podman build -t plant-tracker:latest .
./deploy.sh
```

Container runs internally on port 8472, mapped to host port **5757**. Security: rootless Podman, read-only filesystem, all capabilities dropped, subordinate UID namespace (`--user 1000:1000`), `--network pasta:--ipv4-only`, no-new-privileges, Podman secrets for Telegram.

### systemd auto-start

The container is managed by a systemd user service for auto-start on boot:

```bash
systemctl --user status plant-tracker    # check status
systemctl --user restart plant-tracker   # restart via systemd
```

`deploy.sh` manages the container via Podman directly. After `deploy.sh`, Podman owns the container. On next reboot, systemd takes over. To regenerate the service file after changing `deploy.sh`:

```bash
podman generate systemd --name plant-tracker --new \
  > ~/.config/systemd/user/plant-tracker.service
systemctl --user daemon-reload
```

### Data lives on the host

```
~/plant-data/
├── db/plants.db         # SQLite database
├── photos/              # Uploaded plant photos
└── config/settings.json # Non-secret config (city, reminder time)
```

Secrets (Telegram token, chat ID) are stored via `podman secret` — NOT in settings.json or env vars.

### Container environment variables

| Variable | Container default | Description |
|----------|------------------|-------------|
| `PLANTS_DB_PATH` | `/data/db/plants.db` | SQLite database path |
| `PLANTS_SETTINGS_PATH` | `/data/config/settings.json` | Settings file path |
| `PLANTS_PHOTO_DIR` | `/data/photos` | Photo storage directory |
| `PLANTS_FRONTEND_DIR` | `/app/frontend/build` | Compiled frontend path |
| `CLAUDE_CLI_TIMEOUT` | `120` | Timeout in seconds for Claude CLI calls |
| `UV_NO_CACHE` | `1` | Prevents uv cache writes on read-only rootfs |

---

## Runbook: Common Operations

### View logs

```bash
podman logs -f plant-tracker
podman logs --since 1h plant-tracker   # last hour only
```

### Check health

```bash
podman healthcheck run plant-tracker
# or directly:
curl -s http://localhost:5757/api/health
```

### Restart the container

```bash
podman restart plant-tracker
```

### Code change → rebuild → redeploy

```bash
cd ~/plants
git pull
podman build -t plant-tracker:latest .
./deploy.sh    # stops old container, starts new one
```

### Backend-only change (no frontend rebuild needed)

Same as above — the multi-stage build caches the frontend layer if `frontend/` hasn't changed. Rebuild is fast (~20s).

### Frontend-only change

Same as above — Node stage rebuilds but Python stage is cached. Still fast.

### Update Telegram secrets

```bash
# Remove old, create new
podman secret rm telegram_bot_token
echo "NEW_TOKEN" | podman secret create telegram_bot_token -
./deploy.sh   # restart to pick up new secret
```

### Change reminder time or city

Open the app → Settings → change value → Save. Takes effect on next scheduler tick. For reminder time specifically, you need to restart the container (scheduler reads it once at startup):

```bash
podman restart plant-tracker
```

### Back up all data

```bash
cp -r ~/plant-data ~/plant-data-backup-$(date +%Y%m%d)
```

### Restore from backup

```bash
podman stop plant-tracker
cp -r ~/plant-data-backup-YYYYMMDD/* ~/plant-data/
podman start plant-tracker
```

### Reset a stuck "Identifying..." plant

The plant was saved but Claude CLI failed during identification. Check the debug page (Settings → Debug → Claude Logs) to see the error. Options:
1. Delete and re-add the plant through the UI
2. Or check why Claude CLI failed:
   ```bash
   # Test Claude CLI works inside the container
   podman exec plant-tracker claude -p "say hello" --output-format text

   # If it hangs or errors, the host CLI auth may need refreshing:
   claude -p "say hello"   # run on host, re-auth if prompted
   ```

### Debug endpoints

```bash
# Trigger a weather fetch
curl -X POST http://localhost:5757/api/debug/weather/fetch

# Send watering reminder (only if plants are due)
curl -X POST http://localhost:5757/api/debug/reminders/send

# Send preview reminder with fake data (always sends)
curl -X POST http://localhost:5757/api/debug/reminders/preview

# View weather cache
curl http://localhost:5757/api/debug/weather

# View Claude call logs
curl http://localhost:5757/api/debug/claude-logs
```

### Inspect the SQLite database

```bash
sqlite3 ~/plant-data/db/plants.db
.tables
SELECT id, name, species, location FROM plants;
SELECT * FROM watering_schedules;
SELECT * FROM claude_logs ORDER BY created_at DESC LIMIT 5;
.quit
```

---

## Key Design Decisions

- **Claude CLI** invoked as subprocess (`claude -p`), not the SDK. Uses `--json-schema` for structured output (parsed from `structured_output` field in JSON envelope) and `--add-dir` to grant read access to photo directory. 120s timeout prevents hangs.
- **Photos** stored on filesystem, DB holds web path (`/photos/filename`). Served via StaticFiles mount using `PLANTS_PHOTO_DIR` env var.
- **SPA routing**: FastAPI catch-all route at `/{path:path}` serves static files or falls back to `index.html`.
- **Telegram** uses MarkdownV2 for watering reminders (Rick and Morty themed, rotating daily), plain text for test messages. `send_message()` takes optional `parse_mode` param.
- **LLM output validation**: interval clamped to 0.5-90 days, plant_id verified against DB before writes.
- **Background identification**: `asyncio.create_task` with full try/except + logging. Checks plant still exists before writing. Triggers `job_adjust_schedules` immediately after to apply weather-based adjustment.
- **Claude call logging**: every CLI call is logged to `claude_logs` table with task, prompt, response, error, and duration.
- **Plant location**: indoor/balcony toggle affects schedule adjustment — balcony plants get temperature-aware intervals.
- **Secrets**: `settings.py` reads from `/run/secrets/` first (Podman secrets), falls back to `settings.json`. In container mode, Telegram creds come from secrets only.
- **Container networking**: `--user 1000:1000` with `:U` volume mounts for proper subordinate UID ownership. `deploy.sh` stages Claude config to a world-readable copy so the container's subordinate UID can read it. `pasta:--ipv4-only` prevents IPv6 accept-then-reset that breaks Safari with `.local` mDNS.
- **Geocoding**: Open-Meteo geocoding strips country suffix ("London, UK" → "London") as the API doesn't handle the comma format.
- **Weather**: fetches 7 past + 3 forecast days, all included in adjustment query. `INSERT OR REPLACE` on unique date avoids duplicates.

## Common Issues & Debugging

### Plant stuck on "Identifying..."

Check Settings → Debug → Claude Logs for the error. Common causes:
- Empty response: Claude CLI `--json-schema` requires `--output-format json` (not `text`). The structured output is in the `structured_output` field of the JSON envelope.
- Permission denied on photo: `--add-dir` must be passed to grant Claude CLI read access to the photo directory.
- `.claude.json` not found: host `~/.claude.json` must be mounted into the container.

### Photos not loading

Photos are served at `/photos/{filename}` via StaticFiles. Check:
- Photo file exists: `ls ~/plant-data/photos/`
- DB stores web path (`/photos/abc.jpg`), not filesystem path
- Container mount is correct: `podman inspect plant-tracker | grep -A2 photos`
- In dev: Vite proxy must be running (`vite.config.ts` proxies `/photos` to backend)

### Weather/geocoding not working

`weather.py` uses `httpx` async client. Common issues:
- City name with comma ("London, UK") fails geocoding — code strips suffix automatically
- Network unreachable in container — check DNS: `podman exec plant-tracker curl -s https://api.open-meteo.com/v1/forecast?latitude=0&longitude=0&daily=temperature_2m_max`
- Scheduler skips weather fetch if city is empty (not just if lat/lon is 0)

### Telegram test fails

- Test message uses plain text (no parse_mode). Watering reminders use MarkdownV2.
- If 400 error: check bot token is valid, chat ID is correct
- Get your chat ID: message your bot, then `curl https://api.telegram.org/bot<TOKEN>/getUpdates`
- Verify secrets are mounted: `podman exec plant-tracker cat /run/secrets/telegram_bot_token`

### Scheduler not firing

- Reminder time is read once at startup. Changing it in settings requires `podman restart plant-tracker`.
- Weather fetch: daily at 06:00. Reminders: daily at configured time. Schedule adjustment: every 3 days at 07:00.

### Container won't start

```bash
# Check what went wrong
podman logs plant-tracker

# Common: port already in use
podman ps -a | grep 5757

# Common: secrets not created
podman secret ls
# Should show telegram_bot_token and telegram_chat_id
```

## Svelte 5

Frontend uses Svelte 5 syntax: `$state()`, `$derived()`, `$props()`, `{@render children()}`. Do NOT use Svelte 4 patterns (`let x`, `$:`, `export let`, `<slot />`).
