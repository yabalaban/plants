import logging
import httpx

logger = logging.getLogger(__name__)
TELEGRAM_API = "https://api.telegram.org"

async def send_message(bot_token: str, chat_id: str, text: str) -> bool:
    url = f"{TELEGRAM_API}/bot{bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
            resp.raise_for_status()
        return True
    except Exception:
        logger.exception("Failed to send Telegram message")
        return False

def format_watering_reminder(plants: list[dict]) -> str | None:
    if not plants:
        return None
    lines = ["*Time to water your plants!*\n"]
    for p in plants:
        label = " (overdue!)" if p["status"] == "overdue" else ""
        lines.append(f"- {p['name']}{label}")
    return "\n".join(lines)
