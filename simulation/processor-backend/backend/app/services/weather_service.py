# ======================================================
# FloodWatch - Weather Service
# OpenWeather API Integration for HCMC Districts
# ======================================================

import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import httpx
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# ======================================================
# CONFIGURATION
# ======================================================

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "4cfeed8e0b19a6b8886060e9d27bfa82")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

# Cache thời tiết 10 phút (OpenWeather free tier limit)
weather_cache = TTLCache(maxsize=50, ttl=600)

# ======================================================
# HCMC DISTRICTS DATA
# ======================================================

HCMC_DISTRICTS = [
    {"id": "q1", "name": "Quận 1", "lat": 10.7756, "lon": 106.7020},
    {"id": "q3", "name": "Quận 3", "lat": 10.7839, "lon": 106.6852},
    {"id": "q4", "name": "Quận 4", "lat": 10.7584, "lon": 106.7029},
    {"id": "q5", "name": "Quận 5", "lat": 10.7546, "lon": 106.6671},
    {"id": "q6", "name": "Quận 6", "lat": 10.7461, "lon": 106.6358},
    {"id": "q7", "name": "Quận 7", "lat": 10.7340, "lon": 106.7220},
    {"id": "q8", "name": "Quận 8", "lat": 10.7200, "lon": 106.6300},
    {"id": "q10", "name": "Quận 10", "lat": 10.7725, "lon": 106.6680},
    {"id": "q11", "name": "Quận 11", "lat": 10.7667, "lon": 106.6499},
    {"id": "q12", "name": "Quận 12", "lat": 10.8670, "lon": 106.6418},
    {"id": "binh_tan", "name": "Bình Tân", "lat": 10.7650, "lon": 106.6038},
    {"id": "binh_thanh", "name": "Bình Thạnh", "lat": 10.8105, "lon": 106.7092},
    {"id": "go_vap", "name": "Gò Vấp", "lat": 10.8387, "lon": 106.6652},
    {"id": "phu_nhuan", "name": "Phú Nhuận", "lat": 10.8008, "lon": 106.6783},
    {"id": "tan_binh", "name": "Tân Bình", "lat": 10.8014, "lon": 106.6525},
    {"id": "tan_phu", "name": "Tân Phú", "lat": 10.7908, "lon": 106.6280},
    {"id": "thu_duc", "name": "TP. Thủ Đức", "lat": 10.8534, "lon": 106.7639},
    {"id": "binh_chanh", "name": "Bình Chánh", "lat": 10.6833, "lon": 106.5833},
    {"id": "can_gio", "name": "Cần Giờ", "lat": 10.4113, "lon": 106.9534},
    {"id": "cu_chi", "name": "Củ Chi", "lat": 10.9735, "lon": 106.4933},
    {"id": "hoc_mon", "name": "Hóc Môn", "lat": 10.8841, "lon": 106.5930},
    {"id": "nha_be", "name": "Nhà Bè", "lat": 10.6969, "lon": 106.7003},
]

# ======================================================
# WEATHER CONDITION MAPPING
# ======================================================

def map_weather_condition(weather_main: str) -> str:
    """Map OpenWeather condition to our app condition."""
    mapping = {
        "Clear": "sunny",
        "Clouds": "cloudy",
        "Rain": "rainy",
        "Drizzle": "rainy",
        "Thunderstorm": "stormy",
        "Snow": "cloudy",
        "Mist": "cloudy",
        "Fog": "cloudy",
        "Haze": "cloudy",
        "Smoke": "cloudy",
        "Dust": "cloudy",
        "Sand": "cloudy",
        "Ash": "cloudy",
        "Squall": "stormy",
        "Tornado": "stormy",
    }
    return mapping.get(weather_main, "cloudy")

def get_weather_icon(condition: str) -> str:
    """Get emoji icon for weather condition."""
    icons = {
        "sunny": "☀️",
        "cloudy": "☁️",
        "rainy": "🌧️",
        "stormy": "⛈️",
    }
    return icons.get(condition, "🌤️")

def get_day_name_vi(dt: datetime) -> str:
    """Get Vietnamese day name."""
    days = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return days[dt.weekday()]

# ======================================================
# API FUNCTIONS
# ======================================================

async def fetch_current_weather(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """Fetch current weather from OpenWeather API."""
    cache_key = f"current_{lat}_{lon}"
    if cache_key in weather_cache:
        return weather_cache[cache_key]
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{OPENWEATHER_BASE_URL}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "metric",
                    "lang": "vi"
                }
            )
            response.raise_for_status()
            data = response.json()
            weather_cache[cache_key] = data
            return data
    except Exception as e:
        logger.error(f"OpenWeather current API error: {e}")
        return None

async def fetch_forecast(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """Fetch 5-day forecast from OpenWeather API (3-hour intervals)."""
    cache_key = f"forecast_{lat}_{lon}"
    if cache_key in weather_cache:
        return weather_cache[cache_key]
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{OPENWEATHER_BASE_URL}/forecast",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "metric",
                    "lang": "vi",
                    "cnt": 8  # 8 intervals x 3 hours = 24 hours (lấy 5 giờ đầu)
                }
            )
            response.raise_for_status()
            data = response.json()
            weather_cache[cache_key] = data
            return data
    except Exception as e:
        logger.error(f"OpenWeather forecast API error: {e}")
        return None

# ======================================================
# DATA PROCESSING
# ======================================================

def process_current_weather(data: Dict[str, Any], district: Dict[str, Any]) -> Dict[str, Any]:
    """Process current weather data into our format."""
    if not data:
        return None
    
    weather_main = data.get("weather", [{}])[0].get("main", "Clear")
    condition = map_weather_condition(weather_main)
    
    return {
        "id": district["id"],
        "location": district["name"],
        "lat": district["lat"],
        "lon": district["lon"],
        "temperature": round(data.get("main", {}).get("temp", 0)),
        "feelsLike": round(data.get("main", {}).get("feels_like", 0)),
        "humidity": data.get("main", {}).get("humidity", 0),
        "windSpeed": round(data.get("wind", {}).get("speed", 0) * 3.6),  # m/s to km/h
        "condition": condition,
        "conditionText": data.get("weather", [{}])[0].get("description", ""),
        "icon": get_weather_icon(condition),
        "pressure": data.get("main", {}).get("pressure", 0),
        "visibility": data.get("visibility", 10000) / 1000,  # m to km
        "clouds": data.get("clouds", {}).get("all", 0),
        "rain1h": data.get("rain", {}).get("1h", 0),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }

def process_forecast(data: Dict[str, Any], hours: int = 5) -> List[Dict[str, Any]]:
    """Process forecast data - get next N hours."""
    if not data or "list" not in data:
        return []
    
    forecast_list = []
    # Mỗi interval là 3 giờ, lấy 2 intervals = 6 giờ (bao gồm 5 giờ tới)
    intervals_needed = (hours // 3) + 1
    
    for item in data["list"][:intervals_needed + 1]:
        dt = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
        weather_main = item.get("weather", [{}])[0].get("main", "Clear")
        condition = map_weather_condition(weather_main)
        
        forecast_list.append({
            "datetime": dt.isoformat(),
            "hour": dt.strftime("%H:%M"),
            "day": get_day_name_vi(dt),
            "temp": round(item.get("main", {}).get("temp", 0)),
            "tempMin": round(item.get("main", {}).get("temp_min", 0)),
            "tempMax": round(item.get("main", {}).get("temp_max", 0)),
            "humidity": item.get("main", {}).get("humidity", 0),
            "condition": condition,
            "conditionText": item.get("weather", [{}])[0].get("description", ""),
            "icon": get_weather_icon(condition),
            "windSpeed": round(item.get("wind", {}).get("speed", 0) * 3.6),
            "pop": round(item.get("pop", 0) * 100),  # Probability of precipitation (%)
            "rain3h": item.get("rain", {}).get("3h", 0),
        })
    
    return forecast_list

# ======================================================
# MAIN SERVICE FUNCTIONS
# ======================================================

async def get_weather_for_district(district_id: str) -> Optional[Dict[str, Any]]:
    """Get weather data for a specific district."""
    district = next((d for d in HCMC_DISTRICTS if d["id"] == district_id), None)
    if not district:
        return None
    
    current, forecast = await asyncio.gather(
        fetch_current_weather(district["lat"], district["lon"]),
        fetch_forecast(district["lat"], district["lon"])
    )
    
    weather_data = process_current_weather(current, district)
    if weather_data:
        weather_data["forecast"] = process_forecast(forecast, hours=5)
    
    return weather_data

async def get_weather_all_districts() -> List[Dict[str, Any]]:
    """Get weather data for all HCMC districts."""
    tasks = []
    for district in HCMC_DISTRICTS:
        tasks.append(fetch_current_weather(district["lat"], district["lon"]))
    
    results = await asyncio.gather(*tasks)
    
    weather_list = []
    for district, data in zip(HCMC_DISTRICTS, results):
        processed = process_current_weather(data, district)
        if processed:
            weather_list.append(processed)
    
    return weather_list

async def get_weather_with_forecast(district_ids: List[str] = None) -> List[Dict[str, Any]]:
    """Get weather with 5-hour forecast for selected districts."""
    if district_ids:
        districts = [d for d in HCMC_DISTRICTS if d["id"] in district_ids]
    else:
        # Mặc định lấy 6 quận chính
        default_ids = ["q1", "q7", "thu_duc", "binh_thanh", "go_vap", "q12"]
        districts = [d for d in HCMC_DISTRICTS if d["id"] in default_ids]
    
    tasks = []
    for district in districts:
        tasks.append(asyncio.gather(
            fetch_current_weather(district["lat"], district["lon"]),
            fetch_forecast(district["lat"], district["lon"])
        ))
    
    results = await asyncio.gather(*tasks)
    
    weather_list = []
    for district, (current, forecast) in zip(districts, results):
        processed = process_current_weather(current, district)
        if processed:
            processed["forecast"] = process_forecast(forecast, hours=5)
            weather_list.append(processed)
    
    return weather_list

def get_weather_summary(weather_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate weather summary for AI context."""
    if not weather_list:
        return {"summary": "Không có dữ liệu thời tiết"}
    
    avg_temp = sum(w["temperature"] for w in weather_list) / len(weather_list)
    avg_humidity = sum(w["humidity"] for w in weather_list) / len(weather_list)
    
    rainy_districts = [w["location"] for w in weather_list if w["condition"] in ["rainy", "stormy"]]
    high_rain_districts = [w["location"] for w in weather_list if w.get("rain1h", 0) > 5]
    
    # Check forecast for rain
    districts_rain_forecast = []
    for w in weather_list:
        for f in w.get("forecast", []):
            if f.get("pop", 0) > 60 or f.get("condition") in ["rainy", "stormy"]:
                if w["location"] not in districts_rain_forecast:
                    districts_rain_forecast.append(w["location"])
                break
    
    return {
        "avgTemperature": round(avg_temp),
        "avgHumidity": round(avg_humidity),
        "rainyDistricts": rainy_districts,
        "highRainDistricts": high_rain_districts,
        "districtsWithRainForecast": districts_rain_forecast,
        "totalDistricts": len(weather_list),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ======================================================
# UTILITY
# ======================================================

def get_all_districts() -> List[Dict[str, Any]]:
    """Get list of all HCMC districts."""
    return HCMC_DISTRICTS

def clear_weather_cache():
    """Clear weather cache."""
    weather_cache.clear()
    logger.info("Weather cache cleared")
