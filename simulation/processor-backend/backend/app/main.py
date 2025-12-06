# ======================================================
# Crowdsensing Flood Backend - UPDATED VERSION
# ======================================================

import os
import uuid
import logging
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import asyncio
import asyncpg
import json
import requests
from crate import client
from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Request, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from .services.storage import save_files_local
from .services.orion_client import create_crowd_report_entity
from .schemas import CreateReportResult

# ======================================================
# INIT + CONFIG
# ======================================================

load_dotenv()

# Configure logging with proper encoding
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("flood_processor.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Orion-LD config
ORION_LD_URL = os.getenv("ORION_ENTITIES", "http://orion-ld:1026/ngsi-ld/v1/entities")
CONTEXT = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.6.jsonld"
BASE_URL = os.getenv("BASE_URL")

# CrateDB connection config (env)
# Using container name 'cratedb' and default database 'doc' for asyncpg
# In production, set CRATEDB_DSN in environment variables
CRATEDB_DSN = os.getenv(
    "CRATEDB_DSN",
    "postgresql://crate@cratedb:5432/quantumleap"
)

# CrateDB configuration
CRATEDB_HTTP_URL = os.getenv("CRATEDB_HTTP_URL", "http://cratedb:4200")
CRATEDB_USER = os.getenv("CRATEDB_USER", "crate")


# ======================================================
# UTILITIES
# ======================================================

def now_iso() -> str:
    """Get current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()

def validate_location(location: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize location data structure."""
    if not isinstance(location, dict):
        return None
        
    # If it's already a GeoProperty, return as is
    if location.get("type") == "GeoProperty":
        return location
        
    # If it's a direct value, wrap it in GeoProperty
    if "type" in location and "coordinates" in location:
        return {
            "type": "GeoProperty",
            "value": location
        }
    return None

def severity_from_level(level: float, threshold: float) -> str:
    """Determine severity level based on water level and threshold."""
    if level is None:
        return "Unknown"
    if level >= threshold:
        return "Severe"
    if level >= threshold * 0.7:
        return "Medium"
    return "Low"


def compute_flood_severity(water_level: float, threshold: float, trend: float | None = None) -> str:
    """
    Compute flood risk severity using a more realistic multi-factor model:
    - delta: how much water level exceeds threshold
    - trend: rate of increasing water (optional)
    """

    if threshold <= 0:
        threshold = 3.0  # fallback safe default

    delta = water_level - threshold

    # --- Base severity purely from delta ---
    if delta < 0:
        base_severity = "Low"
    elif 0 <= delta < threshold * 0.3:
        base_severity = "Moderate"
    elif threshold * 0.3 <= delta < threshold * 0.8:
        base_severity = "High"
    else:
        base_severity = "Severe"

    # --- Trend adjustment ---
    # trend > 0 means water is rising
    if trend is not None:
        if trend > 0.15:  # fast increase
            if base_severity in ["Low", "Moderate"]:
                base_severity = "High"
        elif trend > 0.05:  # slow increase
            if base_severity == "Low":
                base_severity = "Moderate"

    return base_severity



# ======================================================
# 1. SENSOR ROUTE → FloodRiskSensor
# ======================================================
@app.post("/flood/sensor")
async def process_flood_sensor(request: Request):
    try:
        raw = await request.json()
        logger.info(f"Received sensor data: {json.dumps(raw, indent=2)}")

        # -------- FIX: Unwrap NGSI-LD Notification --------
        if "data" not in raw or len(raw["data"]) == 0:
            raise HTTPException(400, "Invalid NGSI-LD notification format: missing data[]")

        data = raw["data"][0]   # REAL entity from Fiware
        # ---------------------------------------------------

        district = data.get("district", {}).get("value")
        water_level = data.get("waterLevel", {}).get("value")
        threshold = data.get("alertThreshold", {}).get("value", 3.0)
        location = validate_location(data.get("location", {}))
        source_id = data.get("id")

        if not all([water_level is not None, location, source_id]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: waterLevel, location, or id"
            )

        # optional: lấy trend nếu entity có đính kèm
        trend = data.get("waterTrend", {}).get("value")  # cm/hour hoặc m/hour

        severity = compute_flood_severity(water_level, threshold, trend)


        entity = {
            "id": f"urn:ngsi-ld:FloodRiskSensor:{uuid.uuid4()}",
            "type": "FloodRiskSensor",
            "location": location,
            "severity": {"type": "Property", "value": severity},
            "district": {
                    "type": "Property",
                    "value": district
                },
            "waterLevel": {
                "type": "Property",
                "value": water_level,
                "unitCode": "MTR",
                "observedAt": data.get("waterLevel", {}).get("observedAt", now_iso()),
            },
            "alertThreshold": {
                "type": "Property",
                "value": threshold,
                "unitCode": "MTR",
            },
            "confidence": {"type": "Property", "value": "High"},
            "sourceSensor": {"type": "Relationship", "object": source_id},
            "updatedAt": {"type": "Property", "value": now_iso()},
            "@context": CONTEXT,
        }

        headers = {"Content-Type": "application/ld+json"}
        res = requests.post(ORION_LD_URL, json=entity, headers=headers)
        res.raise_for_status()

        logger.info(f"[FloodRiskSensor] {res.status_code} -> {entity['id']}")
        return {"status": "success", "entity_id": entity["id"]}

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")


# ======================================================
# 2. CROWD ROUTE → FloodRiskCrowd
# ======================================================
@app.post("/flood/crowd")
async def process_flood_crowd(request: Request):
    try:
        data = await request.json()
        logger.info(f"[CrowdReport] Incoming data:\n{json.dumps(data, indent=2)}")

        # Extract entity from NGSI-LD notification format
        if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
            entity = data["data"][0]
        else:
            entity = data  # Fallback to direct entity if not in notification format

        # --- Extract required fields from CrowdReport ---
        source_id = entity.get("id")
        
        # Extract address from entity, not data, and ensure it's not None
        address = None
        if "address" in entity:
            if isinstance(entity["address"], dict) and "value" in entity["address"]:
                address = entity["address"]["value"]
            else:
                address = entity["address"]
            logger.info(f"Extracted address: {address}")  # Debug log
            print(f"Extracted address: {address}")
        # Handle waterLevel as NGSI-LD Property
        water_level_obj = entity.get("waterLevel", {})
        water_level = water_level_obj.get("value") if isinstance(water_level_obj, dict) else None
        
        # Handle other properties
        verified = entity.get("verified", {}).get("value", False) if isinstance(entity.get("verified"), dict) else entity.get("verified", False)
        description = entity.get("description", {}).get("value", "") if isinstance(entity.get("description"), dict) else entity.get("description", "")
        photos = entity.get("photos", {}).get("value", []) if isinstance(entity.get("photos"), dict) else entity.get("photos", [])
        timestamp = entity.get("timestamp", {}).get("value", now_iso()) if isinstance(entity.get("timestamp"), dict) else entity.get("timestamp", now_iso())

        # --- Validate location ---
        location_data = entity.get("location")
        if isinstance(location_data, dict) and "value" in location_data:
            location_data = location_data["value"]
            
        location = validate_location(location_data)
        
        if not location or not source_id or water_level is None:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: id, location, or waterLevel"
            )

        # ----------------------------------------------------
        #               RISK CALCULATION LOGIC
        # ----------------------------------------------------

        # Water level → score between 0 - 1
        water_level_score = min(water_level / 2.0, 1.0)

        # Verified gives higher confidence
        verified_score = 1.0 if verified else 0.5

        # Simple NLP severity detection based on keywords
        severity_keywords = ["danger", "strong", "overflow", "stuck", "blocked", "deep"]
        text_severity_score = (
            1.0 if any(w in description.lower() for w in severity_keywords)
            else 0.5 if len(description) > 30
            else 0.1
        )

        # Weighted risk score
        risk_score = round(
            0.6 * water_level_score +
            0.3 * verified_score +
            0.1 * text_severity_score,
            3
        )

        # Risk level mapping
        if risk_score > 0.8:
            risk_level = "Severe"
        elif risk_score > 0.6:
            risk_level = "High"
        elif risk_score > 0.3:
            risk_level = "Moderate"
        else:
            risk_level = "Low"

        # Crowd confidence label
        crowd_confidence = "Verified" if verified else "Likely"

        # ----------------------------------------------------
        #            BUILD FloodRiskCrowd ENTITY
        # ----------------------------------------------------
        entity_id = f"urn:ngsi-ld:FloodRiskCrowd:{uuid.uuid4()}"

        entity = {
            "id": entity_id,
            "type": "FloodRiskCrowd",

            "riskScore": {
                "type": "Property",
                "value": risk_score
            },

            "riskLevel": {
                "type": "Property",
                "value": risk_level
            },

            "waterLevel": {
                "type": "Property",
                "value": water_level,
                "unitCode": "MTR"
            },

            "crowdConfidence": {
                "type": "Property",
                "value": crowd_confidence
            },

            "factors": {
                "type": "Property",
                "value": {
                    "waterLevelFactor": round(water_level_score, 3),
                    "verifiedFactor": verified_score,
                    "textSeverityFactor": round(text_severity_score, 3)
                }
            },
            **(
                {"address": {"type": "Property", "value": address}} 
                if address is not None 
                else {}
            ),
            "sourceReport": {
                "type": "Relationship",
                "object": source_id
            },

            "location": location,

            "calculatedAt": {
                "type": "Property",
                "value": now_iso()
            },

            "@context": CONTEXT
        }

        # ----------------------------------------------------
        #              SEND ENTITY TO ORION-LD
        # ----------------------------------------------------
        headers = {"Content-Type": "application/ld+json"}
        res = requests.post(ORION_LD_URL, json=entity, headers=headers)
        res.raise_for_status()

        logger.info(f"[FloodRiskCrowd] Created entity {entity_id} (Risk={risk_level}, Score={risk_score})")

        return {
            "status": "success",
            "entity_id": entity_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "orion_status": res.status_code,
            "orion_response": res.json() if res.text else None
        }

    except requests.exceptions.RequestException as e:
        msg = f"Orion-LD communication error: {str(e)}"
        logger.error(msg)
        raise HTTPException(status_code=502, detail=msg)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ======================================================
# 3. REPORT ROUTE
# ======================================================
@app.post("/report", response_model=CreateReportResult)
async def report(
    description: str = Form(...),
    reporterId: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    water_level: Optional[float] = Form(None, description="Water level in meters"),
    images: List[UploadFile] = File([], description="Optional images of the flood"),
):
    try:
        image_urls = save_files_local(images, BASE_URL)
        entity_id = create_crowd_report_entity(
            description=description,
            reporterId=reporterId,
            photo_urls=image_urls,
            lat=latitude,
            lng=longitude,
            water_level=water_level
        )
        return {
            "id": entity_id,
            "status": "created",
            "image_urls": image_urls,
            "waterLevel": water_level
        }
    except Exception as e:
        logger.error(f"Error in report endpoint: {str(e)}", exc_info=True)

# ======================================================
# 4. REALTIME WEBSOCKET FOR MAP VISUALIZATION
# ======================================================
async def ensure_tables_exist():
    """Ensure required tables exist in CrateDB"""
    try:
        conn = client.connect(CRATEDB_HTTP_URL, username=CRATEDB_USER)
        cursor = conn.cursor()

        # FloodRiskCrowd table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS doc.etfloodriskcrowd (
            entity_id STRING PRIMARY KEY,
            location_centroid GEO_POINT,
            riskscore DOUBLE,
            risklevel STRING,
            waterlevel DOUBLE,
            calculatedat TIMESTAMP
        ) CLUSTERED INTO 3 SHARDS
        """)

        # FloodRiskSensor table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS doc.etfloodrisksensor (
            entity_id STRING,
            instanceid STRING,
            location_centroid GEO_POINT,
            severity STRING,
            waterlevel DOUBLE,
            updatedat TIMESTAMP,
            PRIMARY KEY (entity_id, instanceid)
        ) CLUSTERED INTO 3 SHARDS
        """)

        logger.info("Ensured CrateDB tables exist")
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error ensuring tables exist: {str(e)}")
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
def execute_query(query, params=None):
    try:
        conn = client.connect(CRATEDB_HTTP_URL, username=CRATEDB_USER)
        cursor = conn.cursor()
        cursor.execute(query, params or [])
        columns = [desc[0] for desc in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        logger.error(f"CrateDB Query ERROR: {str(e)}")
        return []



# ===========================================================
# 2. SNAPSHOT QUERIES
# ===========================================================
def get_snapshot_crowd(limit=300):
    return execute_query(f"""
        SELECT 
            entity_id,
            entity_type,
            longitude(location_centroid) AS lng,
            latitude(location_centroid) AS lat,
            riskscore,
            risklevel,
            waterlevel,
            address,
            calculatedat
        FROM doc.etcrowdreport
        ORDER BY calculatedat DESC
        LIMIT {limit}
    """)



def get_snapshot_sensor(limit=300):
    return execute_query(f"""
        SELECT 
            t.entity_id,
            t.entity_type,
            t.instanceid,
            longitude(t.location_centroid) AS lng,
            latitude(t.location_centroid) AS lat,
            t.severity,
            t.waterlevel,
            t.district,
            t.updatedat
        FROM doc.etfloodrisksensor t
        INNER JOIN (
            SELECT instanceid, MAX(updatedat) AS last_update
            FROM doc.etfloodrisksensor
            GROUP BY instanceid
        ) sub
        ON t.instanceid = sub.instanceid 
        AND t.updatedat = sub.last_update
        ORDER BY updatedat DESC
        LIMIT {limit}
    """)



# ===========================================================
# 3. INCREMENTAL QUERIES
# ===========================================================
def get_crowd_after(timestamp):
    return execute_query("""
        SELECT 
            entity_id,
            entity_type,
            longitude(location_centroid) AS lng,
            latitude(location_centroid) AS lat,
            riskscore,
            risklevel,
            waterlevel,
            address,
            calculatedat
        FROM doc.etcrowdreport
        WHERE calculatedat > ?
        ORDER BY calculatedat DESC
    """, [timestamp])



def get_sensor_after(timestamp):
    return execute_query("""
        SELECT 
            entity_id,
            entity_type,
            instanceid,
            longitude(location_centroid) AS lng,
            latitude(location_centroid) AS lat,
            severity,
            waterlevel,
            district,
            updatedat
        FROM doc.etfloodrisksensor
        WHERE updatedat > ?
        ORDER BY updatedat DESC
    """, [timestamp])



# ===========================================================
# 4. WEBSOCKET HANDLER
# ===========================================================
@app.websocket("/ws/map")
async def websocket_map(ws: WebSocket):
    await ws.accept()

    last_crowd_ts = None
    last_sensor_ts = None

    try:
        while True:
            msg = await ws.receive_text()
            data = json.loads(msg)
            msg_type = data.get("type")

            # STEP 1 — INITIAL SNAPSHOT
            if msg_type == "init":

                crowd = get_snapshot_crowd()
                sensor = get_snapshot_sensor()

                if crowd:
                    last_crowd_ts = crowd[0]["calculatedat"]
                if sensor:
                    last_sensor_ts = sensor[0]["updatedat"]

                await ws.send_text(json.dumps({
                    "type": "snapshot",
                    "crowd": crowd,
                    "sensor": sensor
                }, default=str))

                continue

            # STEP 2 — POLLING
            if msg_type == "poll":

                updates = {"type": "update", "crowd": [], "sensor": []}

                if last_crowd_ts:
                    new_crowd = get_crowd_after(last_crowd_ts)
                    if new_crowd:
                        last_crowd_ts = new_crowd[0]["calculatedat"]
                        updates["crowd"] = new_crowd

                if last_sensor_ts:
                    new_sensor = get_sensor_after(last_sensor_ts)
                    if new_sensor:
                        last_sensor_ts = new_sensor[0]["updatedat"]
                        updates["sensor"] = new_sensor

                if not updates["crowd"] and not updates["sensor"]:
                    continue

                await ws.send_text(json.dumps(updates, default=str))

    except WebSocketDisconnect:
        logger.info("WebSocket closed")
    except Exception as e:
        logger.error(f"WebSocket Error: {str(e)}")

    finally:
        await ws.close()





# ======================================================
# ROOT CHECK
# ======================================================
@app.get("/")
def root():
    return {"message": "FloodWatchX API Service", "status": "operational"}

# Health check endpoint
@app.get("/health")
def health_check():
    try:
        # Test Orion connection
        response = requests.get(f"{ORION_LD_URL}?limit=1", timeout=5)
        response.raise_for_status()
        return {
            "status": "healthy",
            "orion_ld": "connected" if response.ok else "disconnected",
            "timestamp": now_iso()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable"
        )