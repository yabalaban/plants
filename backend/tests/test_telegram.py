import pytest
from unittest.mock import AsyncMock, patch
from app.services.telegram import send_message, format_watering_reminder

def test_format_watering_reminder_single():
    plants = [{"name": "Monstera", "status": "due"}]
    msg = format_watering_reminder(plants)
    assert "Monstera" in msg
    assert "water" in msg.lower()

def test_format_watering_reminder_multiple():
    plants = [{"name": "Monstera", "status": "due"}, {"name": "Fern", "status": "overdue"}]
    msg = format_watering_reminder(plants)
    assert "Monstera" in msg
    assert "Fern" in msg
    assert "overdue" in msg.lower()

def test_format_watering_reminder_escapes_special_chars():
    plants = [{"name": "My *Star* Plant", "status": "due"}]
    msg = format_watering_reminder(plants)
    assert r"\*Star\*" in msg

def test_format_watering_reminder_empty():
    msg = format_watering_reminder([])
    assert msg is None

@pytest.mark.asyncio
async def test_send_message():
    mock_response = AsyncMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {"ok": True}
    with patch("app.services.telegram.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client
        result = await send_message("test-token", "12345", "Hello!")
    assert result is True

@pytest.mark.asyncio
async def test_send_message_failure():
    with patch("app.services.telegram.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("Network error")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client
        result = await send_message("test-token", "12345", "Hello!")
    assert result is False
