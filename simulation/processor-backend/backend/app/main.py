# ======================================================
# Crowdsensing Flood Backend - FIXED VERSION
# ======================================================

import os
import uuid
import datetime
import requests
import httpx
import re
from typing import List, Optional
import json

from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from .services.storage import save_files_local
from .services.orion_client import create_crowd_report_entity
from .schemas import CreateReportResult

load_dotenv()

# ==========================
# CONFIG
# ==========================

BASE_URL = os.getenv("BASE_URL")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

ORION_ENTITIES = os.getenv(
    "ORION_ENTITIES",
    "http://localhost:1026/ngsi-ld/v1/entities"
)

NGSI_CONTEXT = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"

# ==========================
# FastAPI Init
# ==========================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ======================================================
# ENDPOINT 1: WaterLevelObserved → FloodRiskSensor
# ======================================================
# ======================================================
# ENDPOINT 1: WaterLevelObserved → FloodRiskSensor
# ======================================================
@app.post("/flood/sensor")
async def process_sensor(request: Request):
    print("\n================ SENSOR NOTIFICATION RECEIVED ================")

    try:
        body = await request.json()
        print("RAW BODY:", body)
        data = body["data"][0]
    except Exception as e:
        print("❌ ERROR parsing request:", e)
        raise HTTPException(400, f"Invalid NGSI-LD payload: {e}")

    try:
        water_level = data["waterLevel"]["value"]
        sensor_id = data["id"]
        alert_threshold = data.get("alertThreshold", {}).get("value", 0.3)
        coordinates = data["location"]["value"]["coordinates"]
    except Exception as e:
        print("❌ ERROR extracting fields:", e)
        raise HTTPException(400, f"Missing field in sensor data: {e}")

    print(f"Water level = {water_level}, Sensor = {sensor_id}, Coord = {coordinates}")

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
            "value": datetime.datetime.utcnow().isoformat() + "Z"
        },
        "@context": [NGSI_CONTEXT]
    }

    print("\n=== PATCH FloodRiskSensor Payload ===")
    print(json.dumps(payload, indent=4, ensure_ascii=False))

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{ORION_ENTITIES}/{flood_id}/attrs",
                json=payload,
                headers={"Content-Type": "application/ld+json"}
            )
        print("PATCH Status:", resp.status_code)
        print("PATCH Response:", resp.text)
    except Exception as e:
        print("❌ ERROR sending to Orion-LD:", e)
        raise HTTPException(500, f"Orion-LD error: {e}")

    return {"status": "ok", "entity": flood_id}



# ======================================================
# ENDPOINT 2: CrowdReport → FloodRiskCrowd
# ======================================================
@app.post("/flood/crowd")
async def process_crowd(request: Request):
    print("\n================ CROWD NOTIFICATION RECEIVED ================")

    try:
        body = await request.json()
        print("RAW BODY:", body)
        data = body["data"][0]
    except Exception as e:
        print("❌ ERROR parsing request:", e)
        raise HTTPException(400, f"Invalid NGSI-LD payload: {e}")

    try:
        crowd_id = data["id"]
        description = data.get("description", {}).get("value", "")
        verified = data.get("verified", {}).get("value", False)
        timestamp = data.get("timestamp", {}).get("value", datetime.datetime.utcnow().isoformat())
        coordinates = data["location"]["value"]["coordinates"]
    except Exception as e:
        print("❌ ERROR extracting crowd fields:", e)
        raise HTTPException(400, f"Missing field in crowd data: {e}")

    print(f"Crowd ID = {crowd_id}, Verified={verified}, Desc='{description}'")

    # Detect depth
    match = re.search(r"([0-9]+(\.[0-9]+)?)\s*(cm|m)", description, re.IGNORECASE)
    if match:
        value = float(match.group(1))
        unit = match.group(3).lower()
        depth = value / 100 if unit == "cm" else value
    else:
        depth = 0.30 if "ngập nặng" in description else \
                0.10 if "ngập" in description else 0.00

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
            "value": datetime.datetime.utcnow().isoformat() + "Z"
        },
        "@context": [NGSI_CONTEXT]
    }

    print("\n=== CREATE FloodRiskCrowd Payload ===")
    print(json.dumps(payload, indent=4, ensure_ascii=False))

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                ORION_ENTITIES,
                json=payload,
                headers={"Content-Type": "application/ld+json"}
            )
        print("POST Status:", resp.status_code)
        print("POST Response:", resp.text)
    except Exception as e:
        print("❌ ERROR sending to Orion-LD:", e)
        raise HTTPException(500, f"Orion-LD error: {e}")

    return {"status": "ok", "entity": flood_id}



# ======================================================
# ENDPOINT 3: Mobile App Create Report → CrowdReport
# ======================================================
@app.post("/report", response_model=CreateReportResult)
async def report(
    description: str = Form(...),
    reporterId: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    locationId: Optional[str] = Form(None),
    observationId: Optional[str] = Form(None),
    images: List[UploadFile] = File([])
):
    try:
        image_urls = save_files_local(images, BASE_URL)
    except Exception as e:
        raise HTTPException(500, f"Cannot save images: {str(e)}")

    try:
        entity_id = create_crowd_report_entity(
            description=description,
            reporterId=reporterId,
            photo_urls=image_urls,
            lat=latitude,
            lng=longitude,
            location_id=locationId,
            observation_id=observationId
        )
    except Exception as e:
        raise HTTPException(500, f"Orion-LD error: {str(e)}")

    return {"id": entity_id, "status": "created", "image_urls": image_urls}


@app.get("/")
def root():
    return {"message": "CrowdReport API OK"}
