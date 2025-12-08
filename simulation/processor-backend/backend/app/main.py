# ======================================================
# FloodWatch Backend - OPTIMIZED VERSION v3.0
# Fixed based on BACKEND_ISSUES_ANALYSIS.md
# ======================================================

import os
import io
import uuid
import logging
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from contextlib import contextmanager

import asyncio
import requests
from crate import client
from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Request, status, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from cachetools import TTLCache
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .services.storage import save_files_local, validate_and_save_files
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

app = FastAPI(title="FloodWatch API", version="3.0.0")

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

# CrateDB configuration
CRATEDB_HTTP_URL = os.getenv("CRATEDB_HTTP_URL", "http://cratedb:4200")
CRATEDB_USER = os.getenv("CRATEDB_USER", "crate")
CRATEDB_DSN = os.getenv("CRATEDB_DSN", "postgresql://crate@cratedb:5432/quantumleap")

# ======================================================
# CONNECTION POOL - OPTIMIZED
# ======================================================

# Global connection pool (singleton)
_connection_pool = None

def get_connection_pool():
    """Get or create connection pool (lazy initialization)."""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = client.connect(
            CRATEDB_HTTP_URL, 
            username=CRATEDB_USER
        )
    return _connection_pool

@contextmanager
def get_db_cursor():
    """Context manager for database cursor with connection pooling."""
    conn = get_connection_pool()
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()

# ======================================================
# TTL CACHE - OPTIMIZED (thay thế lru_cache)
# ======================================================

# Cache với TTL 30 giây
snapshot_cache = TTLCache(maxsize=10, ttl=30)
sensor_cache = TTLCache(maxsize=10, ttl=30)

def cached_get_snapshot_crowd(limit: int = 1000) -> list:
    """Get crowd snapshot with TTL cache."""
    cache_key = f"crowd_{limit}"
    if cache_key in snapshot_cache:
        return snapshot_cache[cache_key]
    result = get_snapshot_crowd(limit)
    snapshot_cache[cache_key] = result
    return result

def cached_get_snapshot_sensor(limit: int = 1000) -> list:
    """Get sensor snapshot with TTL cache."""
    cache_key = f"sensor_{limit}"
    if cache_key in sensor_cache:
        return sensor_cache[cache_key]
    result = get_snapshot_sensor(limit)
    sensor_cache[cache_key] = result
    return result

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

def validate_coordinates(lat: float, lng: float, precision_check: bool = False) -> bool:
    """
    Validate coordinates for Vietnam with improved bounds.
    
    Vietnam bounds (tighter):
    - North: 23.4°N, South: 8.5°N
    - West: 102.1°E, East: 109.5°E
    """
    if lat is None or lng is None:
        return False
    
    # Check for default/invalid values (GPS default)
    if lat == 0.0 and lng == 0.0:
        return False
    
    # Vietnam bounds (tighter)
    if not (8.5 <= lat <= 23.4 and 102.1 <= lng <= 109.5):
        return False
    
    # Optional precision check
    if precision_check:
        lat_decimals = len(str(lat).split('.')[-1]) if '.' in str(lat) else 0
        lng_decimals = len(str(lng).split('.')[-1]) if '.' in str(lng) else 0
        if lat_decimals < 4 or lng_decimals < 4:
            logger.warning(f"Low precision coordinates: {lat}, {lng}")
    
    return True

# ======================================================
# SEVERITY CALCULATION - FIXED (theo BACKEND_ISSUES_ANALYSIS)
# ======================================================

def compute_flood_severity(water_level: float, threshold: float = None, trend: float = None) -> str:
    """
    ✅ FIXED: Tính severity dựa trên mức nước tuyệt đối và ngữ cảnh Việt Nam
    
    - water_level < 0.2m: Low (dưới 20cm - không đáng lo)
    - water_level 0.2-0.5m: Moderate (20-50cm - cần chú ý)
    - water_level 0.5-1.0m: High (50-100cm - nguy hiểm)
    - water_level > 1.0m: Severe (trên 100cm - rất nguy hiểm)
    """
    # ✅ Phân loại theo mức nước tuyệt đối (Việt Nam context)
    if water_level < 0.2:  # < 20cm
        base_severity = "Low"
    elif water_level < 0.5:  # 20-50cm
        base_severity = "Moderate"
    elif water_level < 1.0:  # 50-100cm
        base_severity = "High"
    else:  # > 100cm
        base_severity = "Severe"
    
    # ✅ Xét threshold (ngưỡng cảnh báo địa phương) nếu có
    if threshold and threshold > 0 and water_level >= threshold:
        if base_severity in ["Low", "Moderate"]:
            base_severity = "High"
    
    # ✅ Xét xu hướng tăng (trend) với ngưỡng thấp hơn
    severity_levels = ["Low", "Moderate", "High", "Severe"]
    current_idx = severity_levels.index(base_severity)
    
    if trend is not None:
        if trend > 0.05:  # Tăng > 5cm/h - nguy hiểm
            if current_idx < len(severity_levels) - 1:
                base_severity = severity_levels[current_idx + 1]
        elif trend > 0.1:  # Tăng > 10cm/h - rất nguy hiểm
            if current_idx < len(severity_levels) - 2:
                base_severity = severity_levels[min(current_idx + 2, 3)]
    
    return base_severity

def severity_from_level(level: float, threshold: float) -> str:
    """Wrapper for backward compatibility."""
    return compute_flood_severity(level, threshold)

# ======================================================
# RISK SCORE CALCULATION - FIXED (theo BACKEND_ISSUES_ANALYSIS)
# ======================================================

def calculate_crowd_risk_score(
    water_level: float,
    description: str = "",
    photos: list = None,
    verified: bool = False
) -> Tuple[float, str, dict]:
    """
    ✅ FIXED: Tính risk score với logic cải tiến
    
    Returns: (risk_score, risk_level, factors)
    """
    photos = photos or []
    
    # ✅ 1. Water level score - phi tuyến tính (quan trọng nhất)
    if water_level < 0.3:
        water_level_score = water_level / 0.3 * 0.3  # 0-0.3
    elif water_level < 0.8:
        water_level_score = 0.3 + (water_level - 0.3) / 0.5 * 0.4  # 0.3-0.7
    else:
        water_level_score = 0.7 + min((water_level - 0.8) / 1.2 * 0.3, 0.3)  # 0.7-1.0
    
    # ✅ 2. Photo evidence score (nhiều ảnh = độ tin cậy cao)
    photo_score = min(len(photos) * 0.25, 1.0) if photos else 0.0
    
    # ✅ 3. Text severity score với keywords tiếng Việt
    severity_keywords_vi = [
        "nguy hiểm", "nghiêm trọng", "ngập sâu", "kẹt xe", "không qua được",
        "nước chảy mạnh", "ngập nặng", "tràn bờ", "sụp đổ", "cứu", "giúp",
        "chết người", "cuốn trôi", "mắc kẹt", "ngập đến", "ngang người",
        "ngập lụt", "khẩn cấp", "nguy cấp"
    ]
    severity_keywords_en = [
        "danger", "severe", "overflow", "stuck", "blocked", "deep",
        "emergency", "flood", "help", "rescue", "dangerous"
    ]
    all_keywords = severity_keywords_vi + severity_keywords_en
    
    description_lower = description.lower() if description else ""
    keyword_matches = sum(1 for w in all_keywords if w in description_lower)
    
    if keyword_matches >= 3:
        text_severity_score = 1.0
    elif keyword_matches >= 1:
        text_severity_score = 0.7
    elif len(description) > 50:
        text_severity_score = 0.4
    elif len(description) > 20:
        text_severity_score = 0.3
    else:
        text_severity_score = 0.1
    
    # ✅ 4. Verified boost (chỉ tăng confidence, không ảnh hưởng quá nhiều)
    verified_boost = 0.15 if verified else 0.0
    
    # ✅ 5. Final risk score với trọng số hợp lý
    risk_score = round(
        0.50 * water_level_score +      # 50% từ mức nước (quan trọng nhất)
        0.25 * text_severity_score +    # 25% từ mô tả
        0.15 * photo_score +            # 15% từ ảnh
        0.10 * (1.0 if verified else 0.5),  # 10% từ verified status
        3
    )
    
    # Clamp to [0, 1]
    risk_score = max(0.0, min(1.0, risk_score))
    
    # ✅ 6. Determine risk level
    if risk_score > 0.75:
        risk_level = "Severe"
    elif risk_score > 0.55:
        risk_level = "High"
    elif risk_score > 0.35:
        risk_level = "Moderate"
    else:
        risk_level = "Low"
    
    factors = {
        "waterLevelFactor": round(water_level_score, 3),
        "textSeverityFactor": round(text_severity_score, 3),
        "photoFactor": round(photo_score, 3),
        "verifiedFactor": round(verified_boost, 3),
        "keywordMatches": keyword_matches
    }
    
    return risk_score, risk_level, factors

# ======================================================
# DATABASE QUERIES - OPTIMIZED with Connection Pool
# ======================================================

def execute_query(query: str, params: list = None) -> list:
    """Execute CrateDB query with connection pooling."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute(query, params or [])
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"CrateDB Query ERROR: {str(e)}")
        # Reset connection pool on error
        global _connection_pool
        _connection_pool = None
        return []

def deduplicate_by_coordinates(records: List[Dict], coord_precision: int = 5) -> List[Dict]:
    """
    Remove duplicate records with same coordinates.
    coord_precision: number of decimal places (5 = ~1.1m accuracy)
    """
    seen = set()
    unique_records = []
    
    for record in records:
        lat = record.get('lat')
        lng = record.get('lng')
        
        if not validate_coordinates(lat, lng):
            continue
        
        coord_key = (round(lat, coord_precision), round(lng, coord_precision))
        
        if coord_key not in seen:
            seen.add(coord_key)
            unique_records.append(record)
    
    return unique_records

# ===========================================================
# SNAPSHOT QUERIES - OPTIMIZED với xóa cũ lấy mới
# ===========================================================

def get_snapshot_crowd(limit: int = 1000) -> list:
    """Get latest crowd reports - chỉ lấy record mới nhất cho mỗi vị trí."""
    records = execute_query(f"""
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
        FROM doc.etfloodriskcrowd
        WHERE location_centroid IS NOT NULL
        AND calculatedat > NOW() - INTERVAL '24 hours'
        ORDER BY calculatedat DESC
        LIMIT {limit}
    """)
    
    # Deduplicate - chỉ giữ record mới nhất cho mỗi tọa độ
    unique_records = deduplicate_by_coordinates(records)
    logger.info(f"Crowd: {len(records)} raw → {len(unique_records)} unique (24h)")
    
    return unique_records

def get_snapshot_sensor(limit: int = 1000) -> list:
    """
    ✅ OPTIMIZED: Get latest sensor data from WaterLevelObserved entities
    Simulator creates WaterLevelObserved entities with zoneId for polygon zones.
    Lấy record mới nhất cho mỗi zone.
    """
    # ✅ FIX: Sử dụng subquery để lấy record mới nhất của mỗi zoneid
    # Tránh vấn đề LIMIT chỉ lấy một số zones đầu alphabet
    records = execute_query(f"""
        SELECT 
            t.entity_id,
            t.entity_type,
            t.zoneid AS sensorinstanceid,
            longitude(t.location_centroid) AS lng,
            latitude(t.location_centroid) AS lat,
            t.waterlevel,
            t.district,
            t.watertrend,
            t.zoneid,
            t.zonename,
            t.reporttype,
            t.time_index
        FROM doc.etwaterlevelobserved t
        INNER JOIN (
            SELECT zoneid, MAX(time_index) as max_time
            FROM doc.etwaterlevelobserved
            WHERE location_centroid IS NOT NULL
            GROUP BY zoneid
        ) latest ON t.zoneid = latest.zoneid AND t.time_index = latest.max_time
        WHERE t.location_centroid IS NOT NULL
        AND latitude(t.location_centroid) BETWEEN 8.5 AND 23.4
        AND longitude(t.location_centroid) BETWEEN 102.1 AND 109.5
        ORDER BY t.zoneid
        LIMIT {limit}
    """)
    
    # Fallback: Try FloodRiskSensor table if WaterLevelObserved is empty
    if not records:
        logger.info("WaterLevelObserved empty, falling back to FloodRiskSensor")
        records = execute_query(f"""
            SELECT 
                t.entity_id,
                t.entity_type,
                t.sensorinstanceid,
                longitude(t.location_centroid) AS lng,
                latitude(t.location_centroid) AS lat,
                t.severity,
                t.waterlevel,
                t.district,
                t.updatedat,
                t.zoneid,
                t.zonename,
                t.watertrend
            FROM doc.etfloodrisksensor t
            WHERE t.location_centroid IS NOT NULL
            AND latitude(t.location_centroid) BETWEEN 8.5 AND 23.4
            AND longitude(t.location_centroid) BETWEEN 102.1 AND 109.5
            ORDER BY t.updatedat DESC
            LIMIT {limit}
        """)
    
    # Deduplicate by zoneId (for polygon zones) or coordinates
    seen_zones = set()
    seen_coords = set()
    unique_records = []
    
    for record in records:
        lat = record.get('lat')
        lng = record.get('lng')
        zone_id = record.get('zoneid')
        
        if not validate_coordinates(lat, lng):
            continue
        
        # Skip nếu đã thấy zone này
        if zone_id:
            if zone_id in seen_zones:
                continue
            seen_zones.add(zone_id)
        else:
            # Fallback to coordinate-based dedup
            coord_key = (round(lat, 4), round(lng, 4))
            if coord_key in seen_coords:
                continue
            seen_coords.add(coord_key)
        
        # ✅ Calculate severity from water level for WaterLevelObserved
        water_level = record.get('waterlevel', 0)
        if not record.get('severity'):
            record['severity'] = compute_flood_severity(water_level)
        
        # ✅ Map updatedat from entity_id timestamp or use current time
        if not record.get('updatedat'):
            record['updatedat'] = now_iso()
        
        unique_records.append(record)
    
    logger.info(f"Sensor: {len(records)} raw → {len(unique_records)} unique zones")
    
    return unique_records

# ===========================================================
# RADIUS FILTER - NEW FEATURE
# ===========================================================

def filter_by_radius(
    records: List[Dict], 
    center_lat: float, 
    center_lng: float, 
    radius_km: float
) -> List[Dict]:
    """
    ✅ NEW: Lọc records theo bán kính từ điểm trung tâm.
    
    Args:
        records: Danh sách records với lat/lng
        center_lat: Vĩ độ tâm
        center_lng: Kinh độ tâm
        radius_km: Bán kính tính bằng km
    
    Returns:
        Danh sách records trong bán kính
    """
    from math import radians, cos, sin, asin, sqrt
    
    def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in km."""
        R = 6371  # Earth radius in km
        
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * asin(sqrt(a))
        
        return R * c
    
    filtered = []
    for record in records:
        lat = record.get('lat')
        lng = record.get('lng')
        
        if lat is None or lng is None:
            continue
        
        distance = haversine(center_lat, center_lng, lat, lng)
        if distance <= radius_km:
            record['distance_km'] = round(distance, 2)
            filtered.append(record)
    
    # Sort by distance
    filtered.sort(key=lambda x: x.get('distance_km', 0))
    
    return filtered

# ===========================================================
# INCREMENTAL QUERIES - OPTIMIZED
# ===========================================================

def get_crowd_after(timestamp) -> list:
    """Get new crowd reports after timestamp."""
    records = execute_query("""
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
        FROM doc.etfloodriskcrowd
        WHERE calculatedat > ?
        AND location_centroid IS NOT NULL
        ORDER BY calculatedat DESC
        LIMIT 100
    """, [timestamp])
    
    return deduplicate_by_coordinates(records)

def get_sensor_after(timestamp) -> list:
    """Get new sensor data after timestamp.
    ✅ FIX: Query từ WaterLevelObserved table với polygon zone fields
    Lấy record mới nhất của mỗi zone.
    """
    # Try WaterLevelObserved first (from simulator polygon zones)
    # Sử dụng subquery để lấy record mới nhất của mỗi zoneid
    records = execute_query("""
        SELECT 
            t.entity_id,
            t.entity_type,
            t.zoneid AS sensorinstanceid,
            longitude(t.location_centroid) AS lng,
            latitude(t.location_centroid) AS lat,
            t.waterlevel,
            t.district,
            t.watertrend,
            t.zoneid,
            t.zonename,
            t.reporttype,
            t.time_index
        FROM doc.etwaterlevelobserved t
        INNER JOIN (
            SELECT zoneid, MAX(time_index) as max_time
            FROM doc.etwaterlevelobserved
            WHERE location_centroid IS NOT NULL
            GROUP BY zoneid
        ) latest ON t.zoneid = latest.zoneid AND t.time_index = latest.max_time
        WHERE t.location_centroid IS NOT NULL
        ORDER BY t.zoneid
        LIMIT 100
    """)
    
    # Add severity and updatedat for each record
    for record in records:
        water_level = record.get('waterlevel', 0)
        record['severity'] = compute_flood_severity(water_level)
        record['updatedat'] = now_iso()
    
    # Fallback to FloodRiskSensor if empty
    if not records:
        records = execute_query("""
            SELECT 
                entity_id,
                entity_type,
                sensorinstanceid,
                longitude(location_centroid) AS lng,
                latitude(location_centroid) AS lat,
                severity,
                waterlevel,
                district,
                updatedat,
                zoneid,
                zonename,
                watertrend
            FROM doc.etfloodrisksensor
            WHERE updatedat > ?
            AND location_centroid IS NOT NULL
            ORDER BY updatedat DESC
            LIMIT 100
        """, [timestamp])
    
    return deduplicate_by_coordinates(records)

# ===========================================================
# DASHBOARD STATISTICS API - ENHANCED
# ===========================================================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(
    lat: Optional[float] = Query(None, description="Center latitude for radius filter"),
    lng: Optional[float] = Query(None, description="Center longitude for radius filter"),
    radius: Optional[float] = Query(None, description="Radius in km", ge=0.1, le=100)
):
    """
    Get aggregated statistics for dashboard.
    ✅ NEW: Hỗ trợ lọc theo bán kính.
    """
    try:
        crowd = cached_get_snapshot_crowd(1000)
        sensor = cached_get_snapshot_sensor(1000)
        
        # ✅ Apply radius filter if provided
        if lat is not None and lng is not None and radius is not None:
            crowd = filter_by_radius(crowd, lat, lng, radius)
            sensor = filter_by_radius(sensor, lat, lng, radius)
            logger.info(f"Filtered by radius {radius}km from ({lat}, {lng})")
        
        total_points = len(crowd) + len(sensor)
        
        # Severity counts
        severe_count = len([r for r in crowd if r.get('risklevel') == 'Severe'])
        severe_count += len([r for r in sensor if r.get('severity') == 'Severe'])
        
        high_count = len([r for r in crowd if r.get('risklevel') == 'High'])
        high_count += len([r for r in sensor if r.get('severity') == 'High'])
        
        medium_count = len([r for r in crowd if r.get('risklevel') in ['Moderate', 'Medium']])
        medium_count += len([r for r in sensor if r.get('severity') in ['Moderate', 'Medium']])
        
        low_count = total_points - severe_count - high_count - medium_count
        
        # Average water level
        all_water_levels = []
        all_water_levels.extend([r.get('waterlevel', 0) for r in crowd if r.get('waterlevel')])
        all_water_levels.extend([r.get('waterlevel', 0) for r in sensor if r.get('waterlevel')])
        avg_water_level = sum(all_water_levels) / len(all_water_levels) if all_water_levels else 0
        
        return {
            "total": total_points,
            "severe": severe_count,
            "high": high_count,
            "medium": medium_count,
            "low": low_count,
            "avgWaterLevel": round(avg_water_level, 2),
            "sensorCount": len(sensor),
            "communityCount": len(crowd),
            "lastUpdated": now_iso(),
            "filter": {
                "lat": lat,
                "lng": lng,
                "radius_km": radius
            } if radius else None
        }
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        raise HTTPException(500, "Failed to get dashboard stats")

@app.get("/api/dashboard/districts")
async def get_district_summary():
    """Get flood summary by district."""
    try:
        sensor_data = cached_get_snapshot_sensor(1000)
        
        districts = {}
        for record in sensor_data:
            district = record.get('district', 'Unknown')
            if district not in districts:
                districts[district] = {
                    'district': district,
                    'total': 0,
                    'severe': 0,
                    'high': 0,
                    'avgWaterLevel': 0,
                    'waterLevels': []
                }
            
            districts[district]['total'] += 1
            severity = record.get('severity', 'Low')
            if severity == 'Severe':
                districts[district]['severe'] += 1
            elif severity == 'High':
                districts[district]['high'] += 1
            
            water_level = record.get('waterlevel', 0)
            if water_level:
                districts[district]['waterLevels'].append(water_level)
        
        result = []
        for district_name, data in districts.items():
            if data['waterLevels']:
                data['avgWaterLevel'] = round(sum(data['waterLevels']) / len(data['waterLevels']), 2)
            del data['waterLevels']
            result.append(data)
        
        result.sort(key=lambda x: (x['severe'], x['high'], x['total']), reverse=True)
        
        return {"districts": result, "timestamp": now_iso()}
    except Exception as e:
        logger.error(f"District summary error: {str(e)}")
        raise HTTPException(500, "Failed to get district summary")

# ===========================================================
# FLOOD DATA API WITH RADIUS - NEW
# ===========================================================

@app.get("/api/flood/nearby")
async def get_nearby_floods(
    lat: float = Query(..., description="Center latitude"),
    lng: float = Query(..., description="Center longitude"),
    radius: float = Query(5.0, description="Radius in km", ge=0.1, le=100),
    limit: int = Query(100, description="Max results", ge=1, le=500)
):
    """
    ✅ NEW API: Lấy dữ liệu ngập trong bán kính.
    User có thể nhập bán kính tùy ý.
    """
    try:
        if not validate_coordinates(lat, lng):
            raise HTTPException(400, "Invalid coordinates for Vietnam")
        
        crowd = cached_get_snapshot_crowd(1000)
        sensor = cached_get_snapshot_sensor(1000)
        
        # Filter by radius
        nearby_crowd = filter_by_radius(crowd, lat, lng, radius)[:limit]
        nearby_sensor = filter_by_radius(sensor, lat, lng, radius)[:limit]
        
        return {
            "center": {"lat": lat, "lng": lng},
            "radius_km": radius,
            "crowd_reports": nearby_crowd,
            "sensor_data": nearby_sensor,
            "total_crowd": len(nearby_crowd),
            "total_sensor": len(nearby_sensor),
            "timestamp": now_iso()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Nearby floods error: {str(e)}")
        raise HTTPException(500, "Failed to get nearby floods")

# ===========================================================
# WEBSOCKET HANDLER - OPTIMIZED
# ===========================================================

@app.websocket("/ws/map")
async def websocket_map(ws: WebSocket):
    """Optimized WebSocket for real-time map updates."""
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
                logger.info("WebSocket: Sending initial snapshot")
                
                # Get radius filter from client if provided
                radius = data.get("radius")
                center_lat = data.get("lat")
                center_lng = data.get("lng")
                
                crowd = cached_get_snapshot_crowd()
                sensor = cached_get_snapshot_sensor()
                
                # Apply radius filter if provided
                if radius and center_lat and center_lng:
                    crowd = filter_by_radius(crowd, center_lat, center_lng, radius)
                    sensor = filter_by_radius(sensor, center_lat, center_lng, radius)
                    logger.info(f"WebSocket: Applied radius filter {radius}km")
                
                # Track timestamps
                if crowd:
                    last_crowd_ts = crowd[0].get("calculatedat")
                if sensor:
                    last_sensor_ts = sensor[0].get("updatedat")
                
                await ws.send_text(json.dumps({
                    "type": "snapshot",
                    "crowd": crowd,
                    "sensor": sensor,
                    "timestamp": now_iso()
                }, default=str))
                
                logger.info(f"Snapshot sent: {len(crowd)} crowd + {len(sensor)} sensor")
                continue
            
            # STEP 2 — POLLING FOR UPDATES
            if msg_type == "poll":
                updates = {"type": "update", "crowd": [], "sensor": [], "timestamp": now_iso()}
                
                if last_crowd_ts:
                    new_crowd = get_crowd_after(last_crowd_ts)
                    if new_crowd:
                        last_crowd_ts = new_crowd[0].get("calculatedat")
                        updates["crowd"] = new_crowd
                
                if last_sensor_ts:
                    new_sensor = get_sensor_after(last_sensor_ts)
                    if new_sensor:
                        last_sensor_ts = new_sensor[0].get("updatedat")
                        updates["sensor"] = new_sensor
                
                if updates["crowd"] or updates["sensor"]:
                    await ws.send_text(json.dumps(updates, default=str))
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
    finally:
        try:
            await ws.close()
        except:
            pass

# ======================================================
# RETRY MECHANISM for Orion-LD
# ======================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException)
)
def send_to_orion(entity: dict) -> requests.Response:
    """Send entity to Orion-LD with retry mechanism."""
    headers = {"Content-Type": "application/ld+json"}
    response = requests.post(ORION_LD_URL, json=entity, headers=headers, timeout=10)
    response.raise_for_status()
    return response

# ======================================================
# SENSOR ROUTE → FloodRiskSensor - FIXED
# ======================================================

@app.post("/flood/sensor")
async def process_flood_sensor(request: Request):
    """Process flood sensor data from IoT devices.
    ✅ NEW: Hỗ trợ polygon zones với zoneId, zoneName
    """
    try:
        raw = await request.json()
        logger.info("Received sensor data")

        if "data" not in raw or len(raw["data"]) == 0:
            raise HTTPException(400, "Invalid NGSI-LD notification format: missing data[]")

        data = raw["data"][0]
        
        district = data.get("district", {}).get("value")
        water_level = data.get("waterLevel", {}).get("value")
        threshold = data.get("alertThreshold", {}).get("value")
        location = validate_location(data.get("location", {}))
        source_id = data.get("id")
        
        # ✅ NEW: Extract polygon zone fields
        zone_id = data.get("zoneId", {}).get("value")
        zone_name = data.get("zoneName", {}).get("value")

        if not all([water_level is not None, location, source_id]):
            raise HTTPException(400, "Missing required fields: waterLevel, location, or id")

        # ✅ FIXED: Dùng hàm compute_flood_severity mới
        trend = data.get("waterTrend", {}).get("value")
        severity = compute_flood_severity(water_level, threshold, trend)

        entity = {
            "id": f"urn:ngsi-ld:FloodRiskSensor:{uuid.uuid4()}",
            "type": "FloodRiskSensor",
            "location": location,
            "severity": {"type": "Property", "value": severity},
            "waterLevel": {
                "type": "Property",
                "value": water_level,
                "unitCode": "MTR",
                "observedAt": data.get("waterLevel", {}).get("observedAt", now_iso()),
            },
            "alertThreshold": {"type": "Property", "value": threshold or 1.0, "unitCode": "MTR"},
            "confidence": {"type": "Property", "value": "High"},
            "sourceSensor": {"type": "Relationship", "object": source_id},
            "updatedAt": {"type": "Property", "value": now_iso()},
            "@context": CONTEXT,
        }
        
        if district:
            entity["district"] = {"type": "Property", "value": district}
        
        # ✅ NEW: Add polygon zone fields if present
        if zone_id:
            entity["zoneId"] = {"type": "Property", "value": zone_id}
        if zone_name:
            entity["zoneName"] = {"type": "Property", "value": zone_name}
        if trend:
            entity["waterTrend"] = {"type": "Property", "value": trend}
        
        # Add sensorInstanceId for deduplication (renamed from instanceId to avoid NGSI-LD reserved keyword conflict)
        entity["sensorInstanceId"] = {"type": "Property", "value": source_id}

        # ✅ Send with retry
        res = send_to_orion(entity)

        logger.info(f"[FloodRiskSensor] Created {entity['id']} | Severity={severity} | WaterLevel={water_level}m")
        
        # Clear cache to get fresh data
        sensor_cache.clear()
        
        return {"status": "success", "entity_id": entity["id"], "severity": severity}

    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Orion-LD communication error: {e}")
        raise HTTPException(502, "Cannot communicate with Orion-LD")
    except Exception as e:
        logger.error(f"Sensor processing error: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")

# ======================================================
# CROWD ROUTE → FloodRiskCrowd - FIXED
# ======================================================

@app.post("/flood/crowd")
async def process_flood_crowd(request: Request):
    """Process crowd-sourced flood reports."""
    try:
        data = await request.json()
        logger.info("[CrowdReport] Processing")

        if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
            entity = data["data"][0]
        else:
            entity = data

        source_id = entity.get("id")
        
        # Extract address
        address = None
        if "address" in entity:
            if isinstance(entity["address"], dict) and "value" in entity["address"]:
                address = entity["address"]["value"]
            else:
                address = entity["address"]
        
        # Extract water level
        water_level_obj = entity.get("waterLevel", {})
        water_level = water_level_obj.get("value") if isinstance(water_level_obj, dict) else None
        
        # Extract other fields
        verified = entity.get("verified", {}).get("value", False) if isinstance(entity.get("verified"), dict) else entity.get("verified", False)
        description = entity.get("description", {}).get("value", "") if isinstance(entity.get("description"), dict) else entity.get("description", "")
        photos = entity.get("photos", {}).get("value", []) if isinstance(entity.get("photos"), dict) else entity.get("photos", [])
        timestamp = entity.get("timestamp", {}).get("value", now_iso()) if isinstance(entity.get("timestamp"), dict) else entity.get("timestamp", now_iso())

        # Validate location
        location_data = entity.get("location")
        if isinstance(location_data, dict) and "value" in location_data:
            location_data = location_data["value"]
            
        location = validate_location(location_data)
        
        if not location or not source_id or water_level is None:
            raise HTTPException(400, "Missing required fields: id, location, or waterLevel")

        # ✅ FIXED: Dùng hàm tính risk score mới
        risk_score, risk_level, factors = calculate_crowd_risk_score(
            water_level=water_level,
            description=description,
            photos=photos,
            verified=verified
        )

        crowd_confidence = "Verified" if verified else "Likely"

        entity_id = f"urn:ngsi-ld:FloodRiskCrowd:{uuid.uuid4()}"

        new_entity = {
            "id": entity_id,
            "type": "FloodRiskCrowd",
            "riskScore": {"type": "Property", "value": risk_score},
            "riskLevel": {"type": "Property", "value": risk_level},
            "waterLevel": {"type": "Property", "value": water_level, "unitCode": "MTR"},
            "crowdConfidence": {"type": "Property", "value": crowd_confidence},
            "factors": {"type": "Property", "value": factors},
            **({"address": {"type": "Property", "value": address}} if address else {}),
            "sourceReport": {"type": "Relationship", "object": source_id},
            "location": location,
            "calculatedAt": {"type": "Property", "value": now_iso()},
            "@context": CONTEXT
        }

        # ✅ Send with retry
        res = send_to_orion(new_entity)

        logger.info(f"[FloodRiskCrowd] Created {entity_id} | Risk={risk_level} | Score={risk_score}")

        # Clear cache
        snapshot_cache.clear()

        return {
            "status": "success",
            "entity_id": entity_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "factors": factors,
            "orion_status": res.status_code
        }

    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Orion-LD error: {str(e)}")
        raise HTTPException(502, "Orion-LD communication error")
    except Exception as e:
        logger.error(f"Crowd processing error: {str(e)}", exc_info=True)
        raise HTTPException(500, "Internal server error")

# ======================================================
# FILE UPLOAD VALIDATION
# ======================================================

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_image(file: UploadFile) -> bytes:
    """Validate uploaded image file."""
    # Check extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Invalid file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Read and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB")
    
    # Verify it's actually an image
    try:
        img = Image.open(io.BytesIO(content))
        img.verify()
    except Exception:
        raise HTTPException(400, "Invalid or corrupted image file")
    
    # Reset file pointer
    await file.seek(0)
    return content

# ======================================================
# REPORT ROUTE - FIXED with validation
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
    """Submit a flood report from mobile app or web."""
    try:
        # ✅ Validate coordinates if provided
        if latitude is not None and longitude is not None:
            if not validate_coordinates(latitude, longitude):
                raise HTTPException(400, "Invalid coordinates for Vietnam")
        
        # ✅ Validate water level
        if water_level is not None and (water_level < 0 or water_level > 20):
            raise HTTPException(400, "Water level must be between 0 and 20 meters")
        
        # ✅ Validate images
        for img in images:
            await validate_image(img)
        
        # Save files
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report submission error: {str(e)}", exc_info=True)
        raise HTTPException(500, "Failed to submit report")

# ===========================================================
# API CITIZEN REPORTS - BÁO CÁO NGƯỜI DÂN
# ===========================================================

@app.get("/api/reports/recent")
async def get_recent_reports(
    limit: int = Query(20, description="Số lượng báo cáo tối đa", ge=1, le=100),
    hours: int = Query(24, description="Lấy báo cáo trong N giờ gần đây", ge=1, le=168)
):
    """
    ✅ API: Lấy danh sách báo cáo người dân gần đây.
    
    Returns:
        - Danh sách báo cáo với thông tin chi tiết
        - Sắp xếp theo thời gian mới nhất trước
    """
    try:
        records = execute_query(f"""
            SELECT 
                entity_id,
                entity_type,
                longitude(location_centroid) AS lng,
                latitude(location_centroid) AS lat,
                riskscore,
                risklevel,
                waterlevel,
                address,
                calculatedat,
                crowdconfidence
            FROM doc.etfloodriskcrowd
            WHERE location_centroid IS NOT NULL
            AND calculatedat > NOW() - INTERVAL '{hours} hours'
            ORDER BY calculatedat DESC
            LIMIT {limit}
        """)
        
        # Format response
        reports = []
        for r in records:
            reports.append({
                "id": r.get("entity_id"),
                "lat": r.get("lat"),
                "lng": r.get("lng"),
                "waterLevel": r.get("waterlevel"),
                "riskScore": r.get("riskscore"),
                "riskLevel": r.get("risklevel"),
                "address": r.get("address"),
                "confidence": r.get("crowdconfidence", "Unknown"),
                "reportedAt": r.get("calculatedat"),
                "type": "community"
            })
        
        return {
            "reports": reports,
            "total": len(reports),
            "hours": hours,
            "timestamp": now_iso()
        }
    except Exception as e:
        logger.error(f"Get recent reports error: {str(e)}")
        raise HTTPException(500, "Failed to get recent reports")


@app.get("/api/reports/{report_id}")
async def get_report_detail(report_id: str):
    """
    ✅ API: Lấy chi tiết một báo cáo cụ thể.
    """
    try:
        records = execute_query("""
            SELECT 
                entity_id,
                entity_type,
                longitude(location_centroid) AS lng,
                latitude(location_centroid) AS lat,
                riskscore,
                risklevel,
                waterlevel,
                address,
                calculatedat,
                crowdconfidence,
                factors
            FROM doc.etfloodriskcrowd
            WHERE entity_id = ?
            LIMIT 1
        """, [report_id])
        
        if not records:
            raise HTTPException(404, "Report not found")
        
        r = records[0]
        return {
            "id": r.get("entity_id"),
            "lat": r.get("lat"),
            "lng": r.get("lng"),
            "waterLevel": r.get("waterlevel"),
            "riskScore": r.get("riskscore"),
            "riskLevel": r.get("risklevel"),
            "address": r.get("address"),
            "confidence": r.get("crowdconfidence"),
            "factors": r.get("factors"),
            "reportedAt": r.get("calculatedat"),
            "type": "community"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get report detail error: {str(e)}")
        raise HTTPException(500, "Failed to get report detail")


# ======================================================
# WEATHER API - OpenWeather Integration
# ======================================================

from .services.weather_service import (
    get_weather_for_district,
    get_weather_all_districts,
    get_weather_with_forecast,
    get_weather_summary,
    get_all_districts,
    HCMC_DISTRICTS
)
from .services.gemini_service import (
    chat_with_weather_ai,
    get_weather_advice,
    analyze_flood_risk,
    clear_session,
    get_session_info
)

@app.get("/api/weather/districts")
async def get_districts_list():
    """Get list of all HCMC districts."""
    return {
        "districts": HCMC_DISTRICTS,
        "total": len(HCMC_DISTRICTS),
        "city": "TP. Hồ Chí Minh"
    }

@app.get("/api/weather/current")
async def get_current_weather(
    district_ids: Optional[str] = Query(None, description="Comma-separated district IDs (e.g., q1,q7,thu_duc)")
):
    """
    Get current weather for HCMC districts.
    If district_ids not provided, returns default 6 main districts.
    """
    try:
        ids = district_ids.split(",") if district_ids else None
        weather_data = await get_weather_with_forecast(ids)
        
        if not weather_data:
            raise HTTPException(503, "Không thể lấy dữ liệu thời tiết từ OpenWeather")
        
        return {
            "success": True,
            "data": weather_data,
            "total": len(weather_data),
            "timestamp": now_iso()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        raise HTTPException(500, f"Lỗi khi lấy dữ liệu thời tiết: {str(e)}")

@app.get("/api/weather/all")
async def get_all_weather():
    """Get current weather for ALL HCMC districts (22 districts)."""
    try:
        weather_data = await get_weather_all_districts()
        
        if not weather_data:
            raise HTTPException(503, "Không thể lấy dữ liệu thời tiết")
        
        summary = get_weather_summary(weather_data)
        
        return {
            "success": True,
            "data": weather_data,
            "summary": summary,
            "total": len(weather_data),
            "timestamp": now_iso()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Weather all API error: {e}")
        raise HTTPException(500, f"Lỗi: {str(e)}")

@app.get("/api/weather/{district_id}")
async def get_district_weather(district_id: str):
    """Get detailed weather for a specific district with 5-hour forecast."""
    try:
        weather_data = await get_weather_for_district(district_id)
        
        if not weather_data:
            raise HTTPException(404, f"Không tìm thấy quận: {district_id}")
        
        return {
            "success": True,
            "data": weather_data,
            "timestamp": now_iso()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"District weather API error: {e}")
        raise HTTPException(500, f"Lỗi: {str(e)}")

# ======================================================
# CHATBOT API - Gemini AI Integration
# ======================================================

from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    success: bool
    response: str
    session_id: str
    timestamp: str
    error: Optional[str] = None

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat với trợ lý AI về thời tiết.
    Tự động lấy dữ liệu thời tiết hiện tại để đưa vào context.
    """
    try:
        # Lấy dữ liệu thời tiết hiện tại để đưa vào context
        weather_data = await get_weather_with_forecast()
        
        # Lấy summary ngập lụt
        flood_data = None
        try:
            crowd = cached_get_snapshot_crowd(100)
            sensor = cached_get_snapshot_sensor(100)
            
            severe_count = len([r for r in crowd if r.get('risklevel') == 'Severe'])
            severe_count += len([r for r in sensor if r.get('severity') == 'Severe'])
            
            high_count = len([r for r in crowd if r.get('risklevel') == 'High'])
            high_count += len([r for r in sensor if r.get('severity') == 'High'])
            
            # Lấy summary từ weather
            summary = get_weather_summary(weather_data) if weather_data else {}
            
            flood_data = {
                "severe": severe_count,
                "high": high_count,
                "total": len(crowd) + len(sensor),
                "rainyDistricts": summary.get("rainyDistricts", []),
                "districtsWithRainForecast": summary.get("districtsWithRainForecast", [])
            }
        except Exception as e:
            logger.warning(f"Could not get flood data for chat context: {e}")
        
        # Gọi Gemini AI
        result = await chat_with_weather_ai(
            user_message=request.message,
            session_id=request.session_id,
            weather_data=weather_data,
            flood_data=flood_data
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        return ChatResponse(
            success=False,
            response="Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi. Vui lòng thử lại!",
            session_id=request.session_id,
            timestamp=now_iso(),
            error=str(e)
        )

@app.post("/api/chat/clear")
async def clear_chat_session(session_id: str = "default"):
    """Clear chat history for a session."""
    clear_session(session_id)
    return {
        "success": True,
        "message": f"Đã xóa lịch sử chat cho session: {session_id}"
    }

@app.get("/api/chat/session/{session_id}")
async def get_chat_session(session_id: str):
    """Get info about a chat session."""
    return get_session_info(session_id)

@app.get("/api/weather/advice")
async def get_quick_advice():
    """Get quick weather advice based on current conditions."""
    try:
        weather_data = await get_weather_with_forecast()
        advice = await get_weather_advice(weather_data)
        
        return {
            "success": True,
            "advice": advice,
            "timestamp": now_iso()
        }
    except Exception as e:
        logger.error(f"Weather advice API error: {e}")
        raise HTTPException(500, f"Lỗi: {str(e)}")

@app.get("/api/flood/risk-analysis")
async def get_flood_risk_analysis():
    """Get AI-powered flood risk analysis."""
    try:
        weather_data = await get_weather_with_forecast()
        
        # Get flood data
        crowd = cached_get_snapshot_crowd(100)
        sensor = cached_get_snapshot_sensor(100)
        
        summary = get_weather_summary(weather_data) if weather_data else {}
        
        flood_data = {
            "severe": len([r for r in crowd if r.get('risklevel') == 'Severe']) + 
                     len([r for r in sensor if r.get('severity') == 'Severe']),
            "high": len([r for r in crowd if r.get('risklevel') == 'High']) + 
                   len([r for r in sensor if r.get('severity') == 'High']),
            "total": len(crowd) + len(sensor),
            "rainyDistricts": summary.get("rainyDistricts", []),
            "districtsWithRainForecast": summary.get("districtsWithRainForecast", [])
        }
        
        analysis = await analyze_flood_risk(weather_data, flood_data)
        
        return {
            "success": True,
            "analysis": analysis,
            "weatherSummary": summary,
            "floodData": flood_data,
            "timestamp": now_iso()
        }
    except Exception as e:
        logger.error(f"Flood risk analysis API error: {e}")
        raise HTTPException(500, f"Lỗi: {str(e)}")

# ======================================================
# ROOT & HEALTH CHECK
# ======================================================

@app.get("/")
def root():
    """API root endpoint."""
    return {
        "message": "FloodWatch API Service",
        "version": "3.2.0",
        "status": "operational",
        "features": [
            "Improved severity calculation (absolute water level)",
            "Vietnamese keywords support",
            "Radius filter support",
            "TTL caching",
            "Connection pooling",
            "Retry mechanism",
            "Image validation",
            "Recent reports API",
            "OpenWeather Integration (HCMC 22 districts)",
            "Gemini AI Chatbot"
        ],
        "endpoints": {
            "health": "/health",
            "websocket": "/ws/map",
            "dashboard_stats": "/api/dashboard/stats",
            "districts": "/api/dashboard/districts",
            "nearby": "/api/flood/nearby",
            "report": "/report",
            "recent_reports": "/api/reports/recent",
            "report_detail": "/api/reports/{report_id}",
            "weather_current": "/api/weather/current",
            "weather_all": "/api/weather/all",
            "weather_district": "/api/weather/{district_id}",
            "weather_districts_list": "/api/weather/districts",
            "weather_advice": "/api/weather/advice",
            "chat": "/api/chat",
            "flood_risk_analysis": "/api/flood/risk-analysis"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    try:
        # Test Orion connection
        orion_ok = False
        try:
            response = requests.get(f"{ORION_LD_URL}?limit=1", timeout=5)
            orion_ok = response.ok
        except:
            pass
        
        # Test CrateDB connection
        cratedb_ok = False
        try:
            test_result = execute_query("SELECT 1 as test")
            cratedb_ok = len(test_result) > 0
        except:
            pass
        
        status = "healthy" if orion_ok and cratedb_ok else "degraded"
        
        return {
            "status": status,
            "orion_ld": "connected" if orion_ok else "disconnected",
            "cratedb": "connected" if cratedb_ok else "disconnected",
            "timestamp": now_iso(),
            "version": "3.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": now_iso()
        }

# ======================================================
# STARTUP/SHUTDOWN EVENTS
# ======================================================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("=" * 60)
    logger.info("FloodWatch Backend v3.0.0 Starting...")
    logger.info(f"Orion-LD: {ORION_LD_URL}")
    logger.info(f"CrateDB: {CRATEDB_HTTP_URL}")
    logger.info("Features: TTL Cache, Connection Pool, Retry, Radius Filter")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global _connection_pool
    if _connection_pool:
        try:
            _connection_pool.close()
        except:
            pass
    logger.info("FloodWatch Backend shutdown complete")
