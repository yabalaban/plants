import hashlib
import logging
from datetime import date

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


_GREETINGS = [
    "Morty\\! *burp* Your plants are dying, Morty\\!",
    "Listen Morty, I\\-I turned myself into a watering can\\! Just kidding, water your plants\\.",
    "Wubba lubba dub dub\\! Translation: water your plants\\.",
    "In infinite universes, Morty, there's one where you water on time\\. This isn't it\\.",
    "I'm a genius, Morty, and even I can't photosynthesize for your plants\\.",
    "Morty, these plants have more will to live than half the Citadel\\. Help them out\\.",
    "Your plants called, Morty\\. They said \\*burp\\* they're thirsty\\.",
    "Don't be like Jerry, Morty\\. Jerry forgets to water plants\\.",
    "I've seen things you wouldn't believe, Morty\\. A wilted fern is the saddest\\.",
    "Morty, the multiverse has spoken\\. It says water your damn plants\\.",
]

_OVERDUE_QUIPS = [
    "are you trying to speedrun plant murder?",
    "even Jerry would've watered by now",
    "this is a crime against botany, Morty",
    "I've seen interdimensional neglect less severe",
    "the plant dimension is filing a complaint",
]


def format_watering_reminder(plants: list[dict]) -> str | None:
    if not plants:
        return None
    # Rotate based on date so it's different each day but deterministic
    day_hash = int(hashlib.md5(date.today().isoformat().encode()).hexdigest(), 16)
    greeting = _GREETINGS[day_hash % len(_GREETINGS)]

    overdue = [p for p in plants if p["status"] == "overdue"]
    due = [p for p in plants if p["status"] != "overdue"]

    lines = [f"🧪 {greeting}\n"]
    if overdue:
        quip = _OVERDUE_QUIPS[day_hash % len(_OVERDUE_QUIPS)]
        lines.append(f"🚨 *OVERDUE* \\({_escape_markdown(quip)}\\):")
        for p in overdue:
            lines.append(f"  💀 {_escape_markdown(p['name'])}")
        lines.append("")
    if due:
        lines.append("💧 *Due today:*")
        for p in due:
            lines.append(f"  🌱 {_escape_markdown(p['name'])}")

    return "\n".join(lines)
