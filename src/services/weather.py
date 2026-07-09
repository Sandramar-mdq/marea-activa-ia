from dataclasses import dataclass
import httpx

from src.config import OPENWEATHER_API_KEY

MDP_LAT = -38.0023
MDP_LON = -57.5575
URL = "https://api.openweathermap.org/data/2.5/weather"


@dataclass
class WeatherData:
    temperature: float
    condition: str
    description: str
    wind_speed_kmh: float


async def fetch_weather() -> WeatherData | None:
    if not OPENWEATHER_API_KEY:
        return None
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            URL,
            params={
                "lat": MDP_LAT,
                "lon": MDP_LON,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
                "lang": "es",
            },
            timeout=10,
        )
    if resp.status_code != 200:
        return None
    data = resp.json()
    return WeatherData(
        temperature=data["main"]["temp"],
        condition=data["weather"][0]["main"],
        description=data["weather"][0]["description"],
        wind_speed_kmh=round(data["wind"]["speed"] * 3.6, 1),
    )
