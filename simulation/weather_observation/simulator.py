import os
import time
import json
import argparse
from datetime import datetime, timezone
import requests

# -----------------------------
# CONFIG
# -----------------------------
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "5dc5a6dcc868a9ee97e820f7bc13e263")
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

ORION_HOST = os.getenv("ORION_HOST", "localhost")
ORION_BASE = f"http://{ORION_HOST}:1026/ngsi-ld/v1"
ORION_ENTITIES = f"{ORION_BASE}/entities"

WEATHER_ENTITY_ID = os.getenv("WEATHER_ENTITY_ID", "urn:ngsi-ld:WeatherObserved:HoChiMinh_District1")
FLOOD_ENTITY_ID = os.getenv("FLOOD_ENTITY_ID", "urn:ngsi-ld:FloodRiskRain:HoChiMinh_District1")

# coords for District 1
LON = float(os.getenv("WEATHER_LON", "106.70098"))
LAT = float(os.getenv("WEATHER_LAT", "10.77653"))

ORION_HEADERS = {
    "Content-Type": "application/ld+json"
}

# -----------------------------
# Helpers
# -----------------------------
def _safe_number(x):
    try:
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return x
        return float(x)
    except Exception:
        return None

def fetch_current_weather(lat: float, lon: float) -> dict:
    params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_KEY, "units": "metric"}
    r = requests.get(OPENWEATHER_URL, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def normalize_weather_entity(data: dict) -> dict:
    main = data.get("main", {})
    wind = data.get("wind", {}) or {}
    rain = data.get("rain", {}) or {}

    temp = main.get("temp")
    humidity = main.get("humidity")
    pressure = main.get("pressure")
    wind_speed = wind.get("speed", 0.0)
    rain_level = rain.get("1h", rain.get("3h", 0.0))

    dt_unix = data.get("dt")
    ts = datetime.utcfromtimestamp(dt_unix).replace(tzinfo=timezone.utc).isoformat() if dt_unix else datetime.now(timezone.utc).isoformat()

    entity = {
        "id": WEATHER_ENTITY_ID,
        "type": "WeatherObserved",
        "location": {
            "type": "GeoProperty",
            "value": {"type": "Point", "coordinates": [LON, LAT]}
        },
        "temperature": {"type": "Property", "value": _safe_number(temp), "observedAt": ts},
        "humidity": {"type": "Property", "value": _safe_number(humidity), "observedAt": ts},
        "pressure": {"type": "Property", "value": _safe_number(pressure), "observedAt": ts},
        "windSpeed": {"type": "Property", "value": _safe_number(wind_speed), "observedAt": ts},
        "rainLevel": {"type": "Property", "value": _safe_number(rain_level), "observedAt": ts},
        "dateObserved": {"type": "Property", "value": ts, "observedAt": ts},
        "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.6.jsonld"
    }
    return entity

def calculate_flood_risk(weather_entity: dict) -> dict:
    """Simple flood risk score based on rainLevel, humidity, windSpeed"""
    rain = _safe_number(weather_entity.get("rainLevel", {}).get("value", 0))
    humidity = _safe_number(weather_entity.get("humidity", {}).get("value", 0))
    wind = _safe_number(weather_entity.get("windSpeed", {}).get("value", 0))

    # Example formula: weighted sum
    score = rain * 0.6 + humidity * 0.3 - wind * 0.1
    # Clamp 0-10
    score = max(0, min(round(score, 2), 10))

    ts = datetime.now(timezone.utc).isoformat()

    entity = {
        "id": FLOOD_ENTITY_ID,
        "type": "FloodRiskRain",
        "location": weather_entity["location"],
        "riskScore": {"type": "Property", "value": score, "observedAt": ts},
        "dateObserved": {"type": "Property", "value": ts, "observedAt": ts},
        "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.6.jsonld"
    }
    return entity

# -----------------------------
# Orion-LD Interaction
# -----------------------------
def create_entity_orion(entity: dict) -> requests.Response:
    return requests.post(ORION_ENTITIES, json=entity, headers=ORION_HEADERS, timeout=15)

def patch_entity_attrs_orion(entity_id: str, attrs_payload: dict) -> requests.Response:
    url = f"{ORION_ENTITIES}/{entity_id}/attrs"
    return requests.patch(url, json=attrs_payload, headers=ORION_HEADERS, timeout=15)

def ensure_entity(entity: dict):
    print(f"[sim] Sending entity: {entity['id']}")
    resp = create_entity_orion(entity)
    if resp.status_code in (200, 201):
        print(f"[sim] Created: {entity['id']}")
        return True
    elif resp.status_code == 409:
        # PATCH attributes with @context (required for application/ld+json)
        attrs = {k: v for k, v in entity.items() if k not in ("id", "type")}
        if "@context" in entity:
            attrs["@context"] = entity["@context"]
        resp2 = patch_entity_attrs_orion(entity["id"], attrs)
        if resp2.status_code in (204, 201):
            print(f"[sim] PATCH success: {entity['id']}")
            return True
        else:
            print(f"[sim] PATCH failed: {resp2.status_code} {resp2.text}")
            return False
    else:
        print(f"[sim] Create failed: {resp.status_code} {resp.text}")
        return False

# -----------------------------
# Main Run
# -----------------------------
def run_once(do_push=True):
    try:
        raw_weather = fetch_current_weather(LAT, LON)
    except Exception as e:
        print(f"[sim] Fetch weather failed: {e}")
        return

    weather_entity = normalize_weather_entity(raw_weather)
    flood_entity = calculate_flood_risk(weather_entity)

    print(json.dumps(weather_entity, indent=2, ensure_ascii=False))
    print(json.dumps(flood_entity, indent=2, ensure_ascii=False))

    if do_push:
        ensure_entity(weather_entity)
        ensure_entity(flood_entity)

def run_loop(interval=300, do_push=True):
    print(f"[sim] Starting loop every {interval}s. Ctrl+C to stop.")
    try:
        while True:
            run_once(do_push)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[sim] Stopped.")

# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weather + FloodRiskRain simulator")
    parser.add_argument("--no-push", action="store_true", help="Only print, don't push to Orion")
    parser.add_argument("--loop", type=int, default=0, help="Loop interval in seconds (0 = run once)")
    parser.add_argument("--lon", type=float, default=LON)
    parser.add_argument("--lat", type=float, default=LAT)
    parser.add_argument("--weather-id", type=str, default=WEATHER_ENTITY_ID)
    parser.add_argument("--flood-id", type=str, default=FLOOD_ENTITY_ID)
    args = parser.parse_args()

    LON, LAT = args.lon, args.lat
    WEATHER_ENTITY_ID, FLOOD_ENTITY_ID = args.weather_id, args.flood_id

    if args.loop > 0:
        run_loop(interval=args.loop, do_push=not args.no_push)
    else:
        run_once(do_push=not args.no_push)