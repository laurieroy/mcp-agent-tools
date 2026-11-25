"""Async Open-Meteo weather client (geocoding + current forecast, no API key)."""

from __future__ import annotations

import httpx

_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT = httpx.Timeout(10.0)

_WMO_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    56: "light freezing drizzle", 57: "dense freezing drizzle",
    61: "slight rain", 63: "moderate rain", 65: "heavy rain",
    66: "light freezing rain", 67: "heavy freezing rain",
    71: "slight snow", 73: "moderate snow", 75: "heavy snow", 77: "snow grains",
    80: "slight rain showers", 81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}

_CURRENT_FIELDS = (
    "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m"
)


async def get_current_weather(
    city: str, *, transport: httpx.AsyncBaseTransport | None = None
) -> str:
    """Fetch current conditions for ``city`` and return a normalized summary.

    ``transport`` lets tests inject ``httpx.MockTransport``; production callers
    leave it ``None``. Returns a ``"Error: ..."`` string on any failure —
    never raises to the caller.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, transport=transport) as client:
            geo = await client.get(
                _GEOCODING_URL,
                params={"name": city, "count": 1, "language": "en", "format": "json"},
            )
            geo.raise_for_status()
            results = geo.json().get("results") or []
            if not results:
                return f"Error: no location found for '{city}'"
            place = results[0]

            forecast = await client.get(
                _FORECAST_URL,
                params={
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "current": _CURRENT_FIELDS,
                    "timezone": "auto",
                },
            )
            forecast.raise_for_status()
            payload = forecast.json()
            current = payload["current"]
            units = payload.get("current_units", {})
    except httpx.HTTPError:
        return "Error: weather service request failed"
    except (KeyError, TypeError, ValueError):
        return "Error: unexpected weather service response"

    conditions = _WMO_CODES.get(current.get("weather_code"), "unknown conditions")
    name = place.get("name", city)
    region = place.get("admin1") or place.get("country") or ""
    location = f"{name}, {region}" if region else name
    return (
        f"Current weather in {location}: {conditions}, "
        f"{current.get('temperature_2m')}{units.get('temperature_2m', '°C')}, "
        f"precipitation {current.get('precipitation')} {units.get('precipitation', 'mm')}, "
        f"wind {current.get('wind_speed_10m')} {units.get('wind_speed_10m', 'km/h')}, "
        f"humidity {current.get('relative_humidity_2m')}%"
    )
