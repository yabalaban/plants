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

# Stage Claude config readable by container's subordinate UID
CLAUDE_STAGE="$DATA_DIR/.claude-stage"
rm -rf "$CLAUDE_STAGE"
mkdir -p "$CLAUDE_STAGE"
cp -a "$HOME/.claude" "$CLAUDE_STAGE/claude-dir"
cp "$HOME/.claude.json" "$CLAUDE_STAGE/claude.json"
chmod -R a+rwX "$CLAUDE_STAGE"

# Make host creds readable so container can live-refresh before each CLI call
chmod a+rX "$HOME/.claude"
chmod a+r "$HOME/.claude/.credentials.json" 2>/dev/null || true

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
  --network pasta:--ipv4-only \
  -p 5757:8472 \
  -v "$DATA_DIR/db":/data/db:rw,U \
  -v "$DATA_DIR/photos":/data/photos:rw,U \
  -v "$DATA_DIR/config":/data/config:rw,U \
  -v "$CLAUDE_STAGE/claude-dir":/home/app/.claude:rw \
  -v "$CLAUDE_STAGE/claude.json":/home/app/.claude.json:ro \
  -v "$HOME/.claude":/host-creds:ro \
  -v "$CLAUDE_BIN":/usr/local/bin/claude:ro \
  --secret telegram_bot_token \
  --secret telegram_chat_id \
  --health-cmd "curl -sf http://localhost:8472/api/health || exit 1" \
  --health-interval 30s \
  --restart on-failure:3 \
  "$IMAGE"

echo "Plant tracker running on port 5757"
echo "Logs:   podman logs -f $NAME"
echo "Stop:   podman stop $NAME"
echo "Health: podman healthcheck run $NAME"
