# Plant Tracker - Development Guide

## Project Overview

Personal plant care PWA. FastAPI backend + SvelteKit frontend + SQLite. Hosted on Raspberry Pi, accessed via VPN (plain HTTP). Single user, no auth.

## Tooling

- **Python deps**: always use `uv` (never pip/venv directly)
- **Tool versions**: managed by `mise` (Python 3.12, Node 22, uv)
- **If uv is missing**: install via `mise install`

## Architecture

```
backend/app/
├── main.py              # FastAPI app, lifespan, static serving, SPA fallback
├── database.py          # SQLite init + async connection (aiosqlite)
├── models.py            # Pydantic request/response models
├── settings.py          # settings.json read/write
├── routers/
│   ├── plants.py        # CRUD + photo upload + background identification
│   └── settings_router.py  # Settings API + Telegram test
└── services/
    ├── claude.py         # Claude CLI subprocess wrapper (120s timeout)
    ├── weather.py        # Open-Meteo geocoding + forecast
    ├── telegram.py       # Telegram Bot API (MarkdownV2 for reminders, plain for test)
    ├── scheduler.py      # APScheduler: weather fetch, reminders, schedule adjustment
    └── watering.py       # Due/overdue calculation
```

Frontend is SvelteKit compiled to static files, served by FastAPI's catch-all route.

## Running

```bash
# Dev (two terminals)
cd backend && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev   # Vite proxies /api and /photos to :8000

# Production
cd frontend && npm run build
cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Tests

```bash
cd backend && uv run pytest -v   # 31 tests
```

## Key Design Decisions

- **Claude CLI** invoked as subprocess (`claude -p`), not the SDK. Image paths are embedded in the prompt text — Claude uses its built-in Read tool to view them.
- **Photos** stored on filesystem, DB holds web path (`/photos/filename`). Served via StaticFiles mount.
- **SPA routing**: FastAPI catch-all route at `/{path:path}` serves static files or falls back to `index.html`. This is why `/plants/1` works — it's not a real file, it's the SPA.
- **Telegram** uses MarkdownV2 for watering reminders (plant names are escaped), plain text for test messages.
- **LLM output validation**: interval clamped to 0.5-90 days, plant_id verified against DB before writes.
- **Background identification**: `asyncio.create_task` with full try/except + logging. Checks plant still exists before writing (handles race with quick delete). 120s timeout on CLI subprocess.

## Common Issues & Debugging

### Plant stuck on "Identifying..."

The background `_identify_and_update` task failed or timed out. Check:

```bash
# Is Claude CLI working?
claude -p "say hello" --output-format text

# Check server logs for the error
journalctl -u plant-tracker --since "5 min ago"
# or if running manually, check terminal output for:
#   "Plant identification failed" or "Claude CLI timed out"
```

The plant is saved to DB immediately (with `species=NULL`). Identification runs async. If it fails, the plant stays with "Identifying..." forever. To retry, delete and re-add the plant.

### Photos not loading

Photos are served at `/photos/{filename}` via StaticFiles. Check:
- Photo file exists in the `photos/` directory (relative to where uvicorn runs)
- DB stores web path (`/photos/abc.jpg`), not filesystem path
- In dev: Vite proxy must be running (`vite.config.ts` proxies `/photos` to backend)

### Weather/geocoding not working

`weather.py` uses `httpx` async client. Common issues:
- `resp.json()` is sync (NOT `await resp.json()`) — this was a bug that was fixed
- Network unreachable on RPi — check DNS/connectivity
- Open-Meteo may rate-limit aggressive requests

### Telegram test fails

- Test message uses plain text (no parse_mode). Watering reminders use MarkdownV2.
- If 400 error: check bot token is valid, chat ID is correct
- Get your chat ID: message your bot, then `curl https://api.telegram.org/bot<TOKEN>/getUpdates`

### Scheduler not firing

- Reminder time is read once at startup. Changing it in settings requires server restart.
- Weather fetch: daily at 06:00. Reminders: daily at configured time. Schedule adjustment: Monday 07:00.
- Logs: `INFO "Scheduler started with 3 jobs"` on startup

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PLANTS_DB_PATH` | `plants.db` | SQLite database path |
| `PLANTS_SETTINGS_PATH` | `settings.json` | Settings file path |
| `PLANTS_PHOTO_DIR` | `./photos` | Photo storage directory |
| `PLANTS_FRONTEND_DIR` | `../frontend/build` | Compiled frontend path |
| `CLAUDE_CLI_TIMEOUT` | `120` | Timeout in seconds for Claude CLI calls |

## Svelte 5

Frontend uses Svelte 5 syntax: `$state()`, `$derived()`, `$props()`, `{@render children()}`. Do NOT use Svelte 4 patterns (`let x`, `$:`, `export let`, `<slot />`).
