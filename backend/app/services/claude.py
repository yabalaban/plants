import asyncio
import json
import logging
import os
import re

logger = logging.getLogger(__name__)


CLI_TIMEOUT = int(os.environ.get("CLAUDE_CLI_TIMEOUT", "120"))


async def _run_claude_cli(prompt: str, image_path: str | None = None) -> str:
    if image_path:
        abs_path = os.path.abspath(image_path)
        prompt = f"Read the image file at {abs_path} and then:\n\n{prompt}"
    cmd = ["claude", "-p", prompt, "--output-format", "text"]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=CLI_TIMEOUT)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise RuntimeError(f"Claude CLI timed out after {CLI_TIMEOUT}s")
    if proc.returncode != 0:
        raise RuntimeError(f"Claude CLI failed: {stderr.decode()}")
    return stdout.decode().strip()


def _extract_json(text: str) -> dict | list:
    fence_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
    if fence_match:
        return json.loads(fence_match.group(1).strip())
    return json.loads(text)


async def identify_plant(photo_path: str) -> dict | None:
    prompt = (
        "Identify this plant from the photo. Return ONLY valid JSON (no other text) "
        "with these fields: species (string, common and Latin name), "
        "confidence (string: high/medium/low), "
        "care_summary (string, 1-2 sentences), "
        "light_preference (string), "
        "base_watering_interval_days (integer, for indoor conditions), "
        "overwatering_signs (string), underwatering_signs (string)."
    )
    try:
        response = await _run_claude_cli(prompt, image_path=photo_path)
        return _extract_json(response)
    except Exception:
        logger.exception("Plant identification failed")
        return None


async def adjust_schedules(plants: list[dict], weather: list[dict]) -> list[dict]:
    prompt = (
        "Given these plants and their current watering schedules:\n"
        f"{json.dumps(plants, indent=2)}\n\n"
        "And this week's weather data:\n"
        f"{json.dumps(weather, indent=2)}\n\n"
        "Return ONLY valid JSON: an array of objects with plant_id (int), "
        "interval_days (number, adjusted watering interval in days), "
        "and reason (string, why the adjustment was made). "
        "If no adjustment is needed for a plant, keep the same interval_days "
        "and set reason to 'no change needed'."
    )
    try:
        response = await _run_claude_cli(prompt)
        return _extract_json(response)
    except Exception:
        logger.exception("Schedule adjustment failed")
        return []
