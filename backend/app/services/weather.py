import logging
import httpx

logger = logging.getLogger(__name__)
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

async def geocode_city(city: str) -> tuple[float, float] | None:
    # Open-Meteo doesn't handle "City, Country" format — use just the city name
    city_name = city.split(",")[0].strip()
    async with httpx.AsyncClient() as client:
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
    async with httpx.AsyncClient() as client:
        resp = await client.get(WEATHER_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    daily = data["daily"]
    return [{"date": daily["time"][i], "temp_high": daily["temperature_2m_max"][i],
             "temp_low": daily["temperature_2m_min"][i], "humidity": daily["relative_humidity_2m_mean"][i],
             "precipitation_mm": daily["precipitation_sum"][i]} for i in range(len(daily["time"]))]
