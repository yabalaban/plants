# Plant Tracker Containerization — Design Spec

Containerize the plant tracker for Raspberry Pi deployment with proper secrets isolation, security hardening, and auto-start on boot.

## Context

- **Target:** Raspberry Pi 4/5 (4GB+ RAM), accessed via VPN (plain HTTP)
- **Container runtime:** Podman (rootless)
- **Build strategy:** Single multi-stage Containerfile (Node builds frontend, Python runs backend)
- **Secrets:** Podman secrets for Telegram credentials
- **Data:** Host bind-mounts for DB, photos, config
- **Claude CLI:** Mounted from host (read-only)

## Containerfile (Multi-Stage Build)

### Stage 1: Frontend Build

```dockerfile
FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
```

### Stage 2: Backend Runtime

```dockerfile
FROM python:3.12-slim AS runtime

# Install uv and curl (for healthcheck)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash app

# Install Python deps
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --no-dev --frozen

# Copy application code
COPY backend/app/ ./app/

# Copy compiled frontend
COPY --from=frontend /build/build /app/frontend/build

# Create data directories (will be overridden by mounts)
RUN mkdir -p /data/db /data/photos /data/config && chown -R app:app /data

# Environment
ENV PLANTS_DB_PATH=/data/db/plants.db
ENV PLANTS_PHOTO_DIR=/data/photos
ENV PLANTS_SETTINGS_PATH=/data/config/settings.json
ENV PLANTS_FRONTEND_DIR=/app/frontend/build
ENV CLAUDE_CLI_TIMEOUT=120
ENV UV_NO_CACHE=1

USER app
EXPOSE 8472

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8472"]
```

Final image ~150MB. No Node runtime, no dev dependencies, no frontend source in the final image.

## Secrets Management

### Podman Secrets (encrypted at rest)

Sensitive values are stored via `podman secret create` and injected as files at `/run/secrets/` inside the container. They are NOT visible in `podman inspect`, environment variables, or `/proc`.

```bash
echo "<telegram-bot-token>" | podman secret create telegram_bot_token -
echo "<telegram-chat-id>"   | podman secret create telegram_chat_id -
```

### Application Changes

`backend/app/settings.py` must be updated to read secrets from `/run/secrets/` when available:

```python
def _read_secret(name: str) -> str | None:
    path = f"/run/secrets/{name}"
    if os.path.exists(path):
        return open(path).read().strip()
    return None
```

`load_settings()` checks Podman secrets first, then falls back to `settings.json` values:

- `telegram_bot_token`: read from `/run/secrets/telegram_bot_token`, override `settings.json` value
- `telegram_chat_id`: read from `/run/secrets/telegram_chat_id`, override `settings.json` value

Non-secret config (city, latitude, longitude, reminder_time, photo_dir) stays in `settings.json`.

The Settings API `PUT /api/settings` continues to work for non-secret fields. Telegram token and chat ID are read-only when running with Podman secrets (the API accepts them but they're overridden by the secret files on next load).

## Host Data Directory

```
~/plant-data/
├── db/
│   └── plants.db          # SQLite database
├── photos/                # Uploaded plant photos
└── config/
    └── settings.json      # Non-secret config (city, reminder time)
```

### Bind Mounts

| Host path | Container path | Mode | Purpose |
|-----------|---------------|------|---------|
| `~/plant-data/db` | `/data/db` | `rw` | SQLite database |
| `~/plant-data/photos` | `/data/photos` | `rw` | Plant photos |
| `~/plant-data/config` | `/data/config` | `rw` | Non-secret settings |
| `~/.claude` | `/home/app/.claude` | `ro` | Claude CLI auth |
| `$(which claude)` | `/usr/local/bin/claude` | `ro` | Claude CLI binary |

Claude CLI is mounted read-only — the container can invoke it but cannot modify host auth.

## Networking

Simple host-to-container port mapping:

```
-p 8472:8472
```

Accessed via VPN at `http://<rpi-ip>:8472`. No TLS needed (VPN provides encryption).

## Security Hardening

All layers are defense-in-depth — each one adds protection independently:

| Layer | Mechanism | What it prevents |
|-------|-----------|-----------------|
| Rootless Podman | Container runs as unprivileged host user | Container escape → host root |
| Non-root user inside | App runs as `app` (uid 1000) | Privilege escalation within container |
| Read-only rootfs | `--read-only` with `--tmpfs /tmp` | Persistent malware, config tampering |
| Drop all capabilities | `--cap-drop=ALL` | Raw sockets, chown, mount, etc. |
| No new privileges | `--security-opt=no-new-privileges` | setuid/setgid escalation |
| RO Claude mount | Claude CLI + auth mounted read-only | Tampering with host Claude auth |
| Podman secrets | Injected as files, not env vars | Secrets leaking via inspect/proc/logs |
| Health check | Curl to `/api/health` every 30s | Silent failures, zombie processes |
| Restart policy | `--restart on-failure:3` | Transient crashes |

## Deploy Script

`deploy.sh` at the project root wraps the full `podman run` command:

```bash
#!/usr/bin/env bash
set -euo pipefail

IMAGE="plant-tracker:latest"
NAME="plant-tracker"
DATA_DIR="${PLANT_DATA_DIR:-$HOME/plant-data}"

# Ensure data directories exist
mkdir -p "$DATA_DIR"/{db,photos,config}

# Stop existing container if running
podman stop "$NAME" 2>/dev/null || true
podman rm "$NAME" 2>/dev/null || true

# Run
podman run -d \
  --name "$NAME" \
  --read-only \
  --tmpfs /tmp \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --user 1000:1000 \
  -p 8472:8472 \
  -v "$DATA_DIR/db":/data/db:rw \
  -v "$DATA_DIR/photos":/data/photos:rw \
  -v "$DATA_DIR/config":/data/config:rw \
  -v "$HOME/.claude":/home/app/.claude:ro \
  -v "$(mise which claude)":/usr/local/bin/claude:ro \
  --secret telegram_bot_token \
  --secret telegram_chat_id \
  --health-cmd "curl -sf http://localhost:8472/api/health || exit 1" \
  --health-interval 30s \
  --restart on-failure:3 \
  "$IMAGE"

echo "Plant tracker running on port 8472"
echo "Logs: podman logs -f $NAME"
```

## Auto-Start on Boot

Generate a systemd user unit from the Podman container:

```bash
podman generate systemd --name plant-tracker --new > ~/.config/systemd/user/plant-tracker.service
systemctl --user enable plant-tracker
loginctl enable-linger $USER   # keeps user services running after logout
```

This gives systemd management (start/stop/status/journal) while keeping Podman rootless.

## Build & Deploy Workflow

```bash
# On RPi (one-time setup)
mkdir -p ~/plant-data/{db,photos,config}
echo "<token>" | podman secret create telegram_bot_token -
echo "<chat_id>" | podman secret create telegram_chat_id -

# Build
git clone <repo> plants && cd plants
podman build -t plant-tracker:latest .

# Deploy
./deploy.sh

# Useful commands
podman logs -f plant-tracker
podman exec plant-tracker curl -s localhost:8472/api/health
podman stop plant-tracker
podman start plant-tracker
```

## Changes Required to Existing Code

1. **`backend/app/settings.py`** — Add `_read_secret()` helper, update `load_settings()` to merge Podman secrets over `settings.json` values for `telegram.bot_token` and `telegram.chat_id`
2. **`Containerfile`** — New file at project root (multi-stage build as described above)
3. **`deploy.sh`** — New file at project root (deployment script)
4. **`.containerignore`** — Exclude `.git`, `node_modules`, `.venv`, `__pycache__`, `*.db`, `photos/`, `.superpowers/`
5. **`README.md`** — Add container deployment section with Podman setup, secrets creation, build, deploy, and management commands
