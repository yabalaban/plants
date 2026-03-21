import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

async def geocode_city(city: str) -> tuple[float, float] | None:
    # Open-Meteo doesn't handle "City, Country" format — use just the city name
    city_name = city.split(",")[0].strip()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(GEOCODE_URL, params={"name": city_name, "count": 1})
        resp.raise_for_status()
        data = resp.json()
    results = data.get("results", [])
    if not results:
        return None
    return results[0]["latitude"], results[0]["longitude"]

async def fetch_weather(latitude: float, longitude: float, days: int = 7) -> list[dict]:
    params = {
        "latitude": latitude, "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,relative_humidity_2m_mean,precipitation_sum",
        "past_days": days, "forecast_days": 3,
    }
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(WEATHER_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
            if attempt > 1:
                logger.info("Weather fetch succeeded on attempt %d", attempt)
            daily = data["daily"]
            return [{"date": daily["time"][i], "temp_high": daily["temperature_2m_max"][i],
                     "temp_low": daily["temperature_2m_min"][i], "humidity": daily["relative_humidity_2m_mean"][i],
                     "precipitation_mm": daily["precipitation_sum"][i]} for i in range(len(daily["time"]))]
        except (httpx.TimeoutException, httpx.HTTPStatusError) as exc:
            last_exc = exc
            logger.warning("Weather fetch attempt %d/%d failed: %s", attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)
    raise last_exc  # type: ignore[misc]
