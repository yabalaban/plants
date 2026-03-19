import logging
import httpx

logger = logging.getLogger(__name__)
TELEGRAM_API = "https://api.telegram.org"

async def send_message(bot_token: str, chat_id: str, text: str, parse_mode: str | None = None) -> bool:
    url = f"{TELEGRAM_API}/bot{bot_token}/sendMessage"
    payload: dict = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
        return True
    except Exception:
        logger.exception("Failed to send Telegram message")
        return False

def _escape_markdown(text: str) -> str:
    """Escape Telegram MarkdownV2 special characters."""
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


def format_watering_reminder(plants: list[dict]) -> str | None:
    if not plants:
        return None
    lines = ["*Time to water your plants\\!*\n"]
    for p in plants:
        name = _escape_markdown(p["name"])
        label = " \\(overdue\\!\\)" if p["status"] == "overdue" else ""
        lines.append(f"\\- {name}{label}")
    return "\n".join(lines)
