# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

from fastapi import FastAPI, Request
import httpx
import uuid
import re
from datetime import datetime

app = FastAPI()

ORION_BASE = "http://orion-ld:1026/ngsi-ld/v1"
ORION_ENTITIES = f"{ORION_BASE}/entities"
ORION_SUBSCRIPTIONS = f"{ORION_BASE}/subscriptions"

NGSI_CONTEXT = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"

# ======================================================
# AUTO REGISTER NGSI-LD SUBSCRIPTIONS
# ======================================================
@app.on_event("startup")
async def create_subscriptions():

    async with httpx.AsyncClient() as client:

        # ----------------------------------------------------
        # Subscription: WaterLevelObserved → /flood/sensor
        # ----------------------------------------------------
        sub_sensor = {
            "id": f"urn:ngsi-ld:Subscription:WaterLevelObserved",
            "type": "Subscription",
            "entities": [{"type": "WaterLevelObserved"}],
            "notification": {
                "attributes": [
                    "https://schema.org/waterLevel",
                    "https://uri.fiware.org/ns/data-models#location",
                    "https://example.org/alertThreshold",
                    "https://uri.etsi.org/ngsi-ld/createdAt"
                ],
                "endpoint": {
                    "uri": "http://risk-engine:8000/flood/sensor",
                    "accept": "application/json"
                }
            },
            "isActive": True,
            "@context": [NGSI_CONTEXT]
        }

        await client.put(
            f"{ORION_SUBSCRIPTIONS}/{sub_sensor['id']}",
            json=sub_sensor,
            headers={"Content-Type": "application/ld+json"}
        )

        # ----------------------------------------------------
        # Subscription: CrowdReport → /flood/crowd
        # ----------------------------------------------------
        sub_crowd = {
            "id": f"urn:ngsi-ld:Subscription:CrowdReport",
            "type": "Subscription",
            "entities": [{"type": "CrowdReport"}],
            "notification": {
                "attributes": [
                    "https://schema.org/description",
                    "https://schema.org/verified",
                    "https://uri.fiware.org/ns/data-models#location",
                    "https://uri.etsi.org/ngsi-ld/createdAt"
                ],
                "endpoint": {
                    "uri": "http://risk-engine:8000/flood/crowd",
                    "accept": "application/json"
                }
            },
            "isActive": True,
            "@context": [NGSI_CONTEXT]
        }

        await client.put(
            f"{ORION_SUBSCRIPTIONS}/{sub_crowd['id']}",
            json=sub_crowd,
            headers={"Content-Type": "application/ld+json"}
        )

    print("🔥 NGSI-LD Subscriptions registered successfully")


# ======================================================
# ENDPOINT 1: WaterLevelObserved → FloodRiskSensor
# ======================================================
@app.post("/flood/sensor")
async def process_sensor(request: Request):
    body = await request.json()
    data = body["data"][0]

    water_level = data["waterLevel"]["value"]
    sensor_id = data["id"]

    alert_threshold = data.get("alertThreshold", {}).get("value", 0.3)
    coordinates = data["location"]["value"]["coordinates"]

    # === severity rules ===
    if water_level >= 1.5:
        severity = "Severe"
    elif water_level >= 0.5:
        severity = "High"
    elif water_level >= 0.2:
        severity = "Medium"
    else:
        severity = "Low"

    alert = "ThresholdExceeded" if water_level >= alert_threshold else "Normal"

    flood_id = f"urn:ngsi-ld:FloodRiskSensor:{sensor_id.split(':')[-1]}"

    payload = {
        "id": flood_id,
        "type": "FloodRiskSensor",
        "severity": {"type": "Property", "value": severity},
        "alert": {"type": "Property", "value": alert},
        "waterLevel": {"type": "Property", "value": water_level},
        "confidence": {"type": "Property", "value": "High"},
        "sourceSensor": {"type": "Relationship", "object": sensor_id},
        "location": {
            "type": "GeoProperty",
            "value": {"type": "Point", "coordinates": coordinates}
        },
        "updatedAt": {
            "type": "Property",
            "value": datetime.utcnow().isoformat()
        },
        "@context": [NGSI_CONTEXT]
    }

    async with httpx.AsyncClient() as client:
        await client.patch(
            f"{ORION_ENTITIES}/{flood_id}",
            json=payload,
            headers={"Content-Type": "application/ld+json"}
        )

    return {"status": "ok", "entity": flood_id}


# ======================================================
# ENDPOINT 2: CrowdReport → FloodRiskCrowd
# ======================================================
@app.post("/flood/crowd")
async def process_crowd(request: Request):
    body = await request.json()
    data = body["data"][0]

    crowd_id = data["id"]
    description = data.get("description", {}).get("value", "")
    verified = data.get("verified", {}).get("value", False)
    timestamp = data.get("timestamp", {}).get("value", datetime.utcnow().isoformat())
    coordinates = data["location"]["value"]["coordinates"]

    # ===== extract depth from description =====
    match = re.search(r"([0-9]+(\.[0-9]+)?)\s*(cm|m)", description, re.IGNORECASE)

    if match:
        value = float(match.group(1))
        unit = match.group(3).lower()
        depth = value / 100 if unit == "cm" else value
    else:
        depth = 0.30 if "ngập nặng" in description else \
                0.10 if "ngập" in description else 0.00

    # ===== severity =====
    severity = "High" if depth >= 0.30 else \
               "Medium" if depth >= 0.15 else "Low"

    confidence = "High" if verified else "Medium"

    flood_id = f"urn:ngsi-ld:FloodRiskCrowd:{uuid.uuid4()}"

    payload = {
        "id": flood_id,
        "type": "FloodRiskCrowd",
        "severity": {"type": "Property", "value": severity},
        "crowdDepth": {"type": "Property", "value": depth},
        "confidence": {"type": "Property", "value": confidence},
        "sourceCrowd": {"type": "Relationship", "object": crowd_id},
        "location": {
            "type": "GeoProperty",
            "value": {"type": "Point", "coordinates": coordinates}
        },
        "timestamp": {"type": "Property", "value": timestamp},
        "updatedAt": {
            "type": "Property",
            "value": datetime.utcnow().isoformat()
        },
        "@context": [NGSI_CONTEXT]
    }

    async with httpx.AsyncClient() as client:
        await client.post(
            ORION_ENTITIES,
            json=payload,
            headers={"Content-Type": "application/ld+json"}
        )

    return {"status": "ok", "entity": flood_id}
