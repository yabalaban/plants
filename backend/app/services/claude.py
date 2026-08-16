import asyncio
import json
import logging
import os
import time

import aiosqlite

from app.database import get_db_path
from app.settings import _read_secret

logger = logging.getLogger(__name__)


CLI_TIMEOUT = int(os.environ.get("CLAUDE_CLI_TIMEOUT", "120"))

# Dedicated API key for headless CLI calls (Podman secret in prod, env var
# for local dev). Kept separate from any interactive Claude Code login so
# this process never touches the host's personal OAuth session/config.
ANTHROPIC_API_KEY = _read_secret("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")

# Ephemeral HOME for the CLI subprocess so it never reads/writes the host's
# ~/.claude config — just its own ~/.claude under /tmp (tmpfs in prod).
CLI_HOME = os.environ.get("CLAUDE_CLI_HOME", "/tmp/claude-cli-home")

IDENTIFY_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "species": {"type": "string", "description": "Common and Latin name"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "care_summary": {"type": "string", "description": "1-2 sentences"},
        "light_preference": {"type": "string"},
        "base_watering_interval_days": {"type": "integer", "minimum": 1, "maximum": 90},
        "overwatering_signs": {"type": "string"},
        "underwatering_signs": {"type": "string"},
    },
    "required": [
        "species", "confidence", "care_summary", "light_preference",
        "base_watering_interval_days", "overwatering_signs", "underwatering_signs",
    ],
})

HEALTH_CHECK_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "overall": {"type": "string", "enum": ["good", "fair", "poor", "critical"]},
        "summary": {"type": "string", "description": "1-2 sentence overall assessment"},
        "issues": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of observed problems, empty if healthy",
        },
        "recommendations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Actionable care suggestions",
        },
    },
    "required": ["overall", "summary", "issues", "recommendations"],
})

ADJUST_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "adjustments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "plant_id": {"type": "integer"},
                    "interval_days": {"type": "number", "minimum": 0.5, "maximum": 90},
                    "reason": {"type": "string"},
                },
                "required": ["plant_id", "interval_days", "reason"],
            },
        },
    },
    "required": ["adjustments"],
})


async def _log_call(task: str, prompt: str, response: str | None, error: str | None, duration_ms: int):
    try:
        async with aiosqlite.connect(get_db_path()) as db:
            await db.execute(
                "INSERT INTO claude_logs (task, prompt, response, error, duration_ms) VALUES (?, ?, ?, ?, ?)",
                (task, prompt, response, error, duration_ms),
            )
            await db.commit()
    except Exception:
        logger.exception("Failed to log Claude call")


async def _run_claude_cli(
    prompt: str,
    *,
    task: str = "unknown",
    image_path: str | None = None,
    schema: str | None = None,
) -> str:
    env = dict(os.environ)
    if ANTHROPIC_API_KEY:
        # Isolated, ephemeral home — API-key auth never touches ~/.claude
        os.makedirs(CLI_HOME, exist_ok=True)
        env["HOME"] = CLI_HOME
        env["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY
    output_format = "json" if schema else "text"
    cmd = ["claude", "-p", prompt, "--output-format", output_format]
    if image_path:
        abs_path = os.path.abspath(image_path)
        prompt = f"Read the image file at {abs_path} and then:\n\n{prompt}"
        cmd = ["claude", "-p", prompt, "--output-format", output_format,
               "--add-dir", os.path.dirname(abs_path)]
    if schema:
        cmd.extend(["--json-schema", schema])
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env,
    )
    t0 = time.monotonic()
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=CLI_TIMEOUT)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        duration_ms = int((time.monotonic() - t0) * 1000)
        error = f"Timed out after {CLI_TIMEOUT}s"
        await _log_call(task, prompt, None, error, duration_ms)
        raise RuntimeError(error)
    duration_ms = int((time.monotonic() - t0) * 1000)
    if proc.returncode != 0:
        error = stderr.decode().strip() or stdout.decode().strip()
        await _log_call(task, prompt, None, error, duration_ms)
        raise RuntimeError(f"Claude CLI failed: {error}")
    raw = stdout.decode().strip()
    if schema:
        envelope = json.loads(raw)
        result = json.dumps(envelope.get("structured_output") or envelope.get("result", ""))
    else:
        result = raw
    await _log_call(task, prompt, result, None, duration_ms)
    return result


async def identify_plant(photo_path: str) -> dict | None:
    prompt = "Identify this plant from the photo."
    try:
        response = await _run_claude_cli(
            prompt, task="identify", image_path=photo_path, schema=IDENTIFY_SCHEMA,
        )
        return json.loads(response)
    except Exception:
        logger.exception("Plant identification failed")
        return None


async def check_plant_health(photo_path: str, species: str | None) -> dict | None:
    context = f" The plant is {species}." if species else ""
    prompt = f"Assess the health of this plant from the photo.{context} Look for signs of disease, pests, nutrient deficiency, overwatering, underwatering, sunburn, or other issues."
    try:
        response = await _run_claude_cli(
            prompt, task="health_check", image_path=photo_path, schema=HEALTH_CHECK_SCHEMA,
        )
        return json.loads(response)
    except Exception:
        logger.exception("Plant health check failed")
        return None


async def adjust_schedules(plants: list[dict], weather: list[dict]) -> list[dict]:
    prompt = (
        "Given these plants and their current watering schedules:\n"
        f"{json.dumps(plants, indent=2)}\n\n"
        "And this week's weather data:\n"
        f"{json.dumps(weather, indent=2)}\n\n"
        "Adjust watering intervals based on weather conditions. "
        "If no adjustment is needed, keep the same interval_days "
        "and set reason to 'no change needed'."
    )
    try:
        response = await _run_claude_cli(prompt, task="adjust_schedules", schema=ADJUST_SCHEMA)
        return json.loads(response)["adjustments"]
    except Exception:
        logger.exception("Schedule adjustment failed")
        return []
