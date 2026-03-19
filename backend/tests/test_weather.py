import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.weather import fetch_weather, geocode_city

MOCK_GEOCODE_RESPONSE = {"results": [{"name": "Amsterdam", "latitude": 52.374, "longitude": 4.8897}]}
MOCK_WEATHER_RESPONSE = {
    "daily": {
        "time": ["2026-03-18"],
        "temperature_2m_max": [18.5], "temperature_2m_min": [8.2],
        "relative_humidity_2m_mean": [72.0], "precipitation_sum": [0.0],
    }
}


def _make_mock_response(data):
    """Create a mock httpx.Response with sync .json() method."""
    resp = MagicMock()
    resp.json.return_value = data
    resp.raise_for_status = MagicMock()
    return resp


@pytest.mark.asyncio
async def test_geocode_city():
    mock_response = _make_mock_response(MOCK_GEOCODE_RESPONSE)
    with patch("app.services.weather.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client
        lat, lon = await geocode_city("Amsterdam")
    assert abs(lat - 52.374) < 0.01
    assert abs(lon - 4.8897) < 0.01

@pytest.mark.asyncio
async def test_geocode_city_not_found():
    mock_response = _make_mock_response({"results": []})
    with patch("app.services.weather.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client
        result = await geocode_city("Nonexistentville")
    assert result is None

@pytest.mark.asyncio
async def test_fetch_weather():
    mock_response = _make_mock_response(MOCK_WEATHER_RESPONSE)
    with patch("app.services.weather.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client
        days = await fetch_weather(52.374, 4.8897)
    assert len(days) == 1
    assert days[0]["date"] == "2026-03-18"
    assert days[0]["temp_high"] == 18.5
