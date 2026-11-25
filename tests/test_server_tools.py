"""Tests 1–3: individual tool execution (§4 Step 5)."""

import httpx

from src.server.tools.math_tool import calculate_expression
from src.server.tools.sql_tool import query_database
from src.server.tools.weather_tool import get_current_weather

_GEO_RESPONSE = {
    "results": [
        {
            "name": "Seattle",
            "admin1": "Washington",
            "country": "United States",
            "latitude": 47.6062,
            "longitude": -122.3321,
        }
    ]
}
_FORECAST_RESPONSE = {
    "current": {
        "temperature_2m": 8.9,
        "relative_humidity_2m": 82,
        "precipitation": 0.4,
        "weather_code": 61,
        "wind_speed_10m": 14.2,
    },
    "current_units": {
        "temperature_2m": "°C",
        "relative_humidity_2m": "%",
        "precipitation": "mm",
        "weather_code": "wmo code",
        "wind_speed_10m": "km/h",
    },
}


async def test_sql_read_accuracy():
    """Test 1: a valid SELECT returns the seeded Seattle SKU-90210 row."""
    result = await query_database(
        "SELECT sku, quantity FROM inventory "
        "WHERE warehouse_city = 'Seattle' AND sku = 'SKU-90210'"
    )
    assert not result.startswith("Error")
    assert "SKU-90210" in result
    assert "500" in result


async def test_weather_api_integration():
    """Test 2: mocked Open-Meteo payload is normalized into a summary."""

    def handler(request: httpx.Request) -> httpx.Response:
        if "geocoding-api" in str(request.url):
            return httpx.Response(200, json=_GEO_RESPONSE)
        return httpx.Response(200, json=_FORECAST_RESPONSE)

    result = await get_current_weather(
        "Seattle", transport=httpx.MockTransport(handler)
    )
    assert not result.startswith("Error")
    assert "Seattle" in result
    assert "8.9" in result
    assert "slight rain" in result
    assert "precipitation 0.4" in result


def test_math_evaluator_precision():
    """Test 3: order of operations, precedence, and whitelisted functions."""
    assert calculate_expression("2 + 3 * (4 - 1) ** 2") == "29"
    assert calculate_expression("10 - 2 * 3") == "4"
    assert calculate_expression("2 ** 3 ** 2") == "512"  # right-associative
    assert calculate_expression("(8 + 2) / 5") == "2"
    assert calculate_expression("sqrt(16) + abs(-3)") == "7"
    assert calculate_expression("round(pi, 2)") == "3.14"
