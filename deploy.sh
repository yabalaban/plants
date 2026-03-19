#!/usr/bin/env bash
set -euo pipefail

IMAGE="plant-tracker:latest"
NAME="plant-tracker"
DATA_DIR="${PLANT_DATA_DIR:-$HOME/plant-data}"

# Resolve Claude CLI path (mise shim or direct)
CLAUDE_BIN="$(mise which claude 2>/dev/null || which claude)"
if [ ! -f "$CLAUDE_BIN" ]; then
    echo "Error: claude CLI not found. Install and authenticate it first."
    exit 1
fi

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
  -v "$CLAUDE_BIN":/usr/local/bin/claude:ro \
  --secret telegram_bot_token \
  --secret telegram_chat_id \
  --health-cmd "curl -sf http://localhost:8472/api/health || exit 1" \
  --health-interval 30s \
  --restart on-failure:3 \
  "$IMAGE"

echo "Plant tracker running on port 8472"
echo "Logs:   podman logs -f $NAME"
echo "Stop:   podman stop $NAME"
echo "Health: podman healthcheck run $NAME"
