# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

"""
FloodWatch Subscription Manager v2.0
=====================================
✅ OPTIMIZED: Loại bỏ duplicate subscriptions
✅ Mỗi entity type chỉ có 1 subscription chính
"""

import os
import requests
import time

# Get environment variables with defaults
ORION_HOST = os.getenv("ORION_HOST", "orion-ld")
QL_HOST = os.getenv("QL_HOST", "quantumleap")
API_HOST = os.getenv("API_HOST", "floodwatch-api")

# Build URLs from environment
ORION_URL = f"http://{ORION_HOST}:1026/ngsi-ld/v1/subscriptions"
QL_NOTIFY_URL = f"http://{QL_HOST}:8668/v2/notify"
API_BASE_URL = f"http://{API_HOST}:8000"

CONTEXT = [
    "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.6.jsonld"
]

def delete_subscription(sub_id: str) -> bool:
    """Delete a subscription by ID."""
    try:
        delete_url = f"{ORION_URL}/{sub_id}"
        res = requests.delete(delete_url, timeout=10)
        return res.status_code in (204, 404)
    except Exception as e:
        print(f"⚠ Error deleting {sub_id}: {e}")
        return False

def list_subscriptions() -> list:
    """List all existing subscriptions."""
    try:
        res = requests.get(ORION_URL, timeout=10)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception as e:
        print(f"⚠ Error listing subscriptions: {e}")
        return []

def cleanup_old_subscriptions():
    """Remove old/duplicate subscriptions."""
    print("\n🧹 Cleaning up old subscriptions...")
    existing = list_subscriptions()
    
    # IDs to keep (new optimized ones)
    keep_ids = {
        # FastAPI Processing subscriptions
        "urn:ngsi-ld:Subscription:WaterLevelObserved-Process",
        "urn:ngsi-ld:Subscription:CrowdReport-Process",
        "urn:ngsi-ld:Subscription:WeatherObserved-Process",
        # QuantumLeap Storage subscriptions  
        "urn:ngsi-ld:Subscription:WaterLevelObserved-Storage",
        "urn:ngsi-ld:Subscription:CrowdReport-Storage",
        "urn:ngsi-ld:Subscription:CameraStream-Storage",
        "urn:ngsi-ld:Subscription:FloodRiskSensor-Storage",
        "urn:ngsi-ld:Subscription:FloodRiskCrowd-Storage",
        "urn:ngsi-ld:Subscription:WeatherObserved-Storage",
        "urn:ngsi-ld:Subscription:FloodRiskRain-Storage",
    }
    
    deleted = 0
    for sub in existing:
        sub_id = sub.get("id", "")
        if sub_id not in keep_ids:
            if delete_subscription(sub_id):
                print(f"  🗑 Deleted old: {sub_id}")
                deleted += 1
    
    print(f"  Cleaned up {deleted} old subscriptions")

def create_subscription(payload: dict, name: str) -> bool:
    """Create a single subscription with retry."""
    headers = {"Content-Type": "application/ld+json"}
    sub_id = payload.get("id")
    
    for attempt in range(3):
        try:
            res = requests.post(ORION_URL, json=payload, headers=headers, timeout=10)
            
            if res.status_code in (200, 201):
                print(f"✔ Created: {name}")
                return True
            elif res.status_code == 409:
                # Already exists - delete and recreate
                if delete_subscription(sub_id):
                    time.sleep(0.5)
                    res = requests.post(ORION_URL, json=payload, headers=headers, timeout=10)
                    if res.status_code in (200, 201):
                        print(f"✔ Recreated: {name}")
                        return True
            
            print(f"❌ Failed ({res.status_code}): {name}")
            print(f"   Response: {res.text[:200]}")
            
        except Exception as e:
            print(f"⚠ Attempt {attempt + 1} failed for {name}: {e}")
            time.sleep(1)
    
    return False

def register_processing_subscriptions():
    """
    ✅ OPTIMIZED: Register subscriptions for FastAPI processing.
    Chỉ tạo subscription cho các entity cần xử lý real-time.
    """
    print("\n📡 Registering Processing Subscriptions (FastAPI)...")
    
    subscriptions = [
        {
            "id": "urn:ngsi-ld:Subscription:WaterLevelObserved-Process",
            "name": "WaterLevelObserved → FloodRiskSensor",
            "entity_type": "WaterLevelObserved",
            "endpoint": f"{API_BASE_URL}/flood/sensor",
            # ✅ FIX: Added zoneId, zoneName, reportType for polygon zones
            "attributes": ["waterLevel", "location", "status", "alertThreshold", "district", "waterTrend", "zoneId", "zoneName", "reportType"]
        },
        {
            "id": "urn:ngsi-ld:Subscription:CrowdReport-Process",
            "name": "CrowdReport → FloodRiskCrowd", 
            "entity_type": "CrowdReport",
            "endpoint": f"{API_BASE_URL}/flood/crowd",
            "attributes": [
                "reporterId", "description", "photos", "timestamp", "waterLevel",
                "verified", "location", "address"
            ]
        },
        {
            "id": "urn:ngsi-ld:Subscription:WeatherObserved-Process",
            "name": "WeatherObserved → Processing",
            "entity_type": "WeatherObserved",
            "endpoint": f"{API_BASE_URL}/weather/notify",
            "attributes": ["temperature", "humidity", "pressure", "windSpeed", "rainLevel", "dateObserved"]
        }
    ]

    success = 0
    for sub in subscriptions:
        payload = {
            "id": sub["id"],
            "type": "Subscription",
            "status": "active",
            "entities": [{"type": sub["entity_type"]}],
            "notification": {
                "endpoint": {
                    "uri": sub["endpoint"],
                    "accept": "application/ld+json"
                },
                "attributes": sub["attributes"]
            },
            "watchedAttributes": sub["attributes"],
            "name": sub["name"],
            "@context": CONTEXT
        }
        
        if create_subscription(payload, sub["name"]):
            success += 1
    
    print(f"  Processing subscriptions: {success}/{len(subscriptions)} created")
    return success

def register_storage_subscriptions():
    """
    ✅ OPTIMIZED: Register subscriptions for QuantumLeap storage.
    Lưu trữ tất cả entity types vào CrateDB.
    """
    print("\n💾 Registering Storage Subscriptions (QuantumLeap)...")
    
    subscriptions = [
        # Raw data entities (source data)
        {
            "id": "urn:ngsi-ld:Subscription:WaterLevelObserved-Storage",
            "name": "WaterLevelObserved → Storage",
            "entity_type": "WaterLevelObserved",
            # ✅ FIX: Added zoneId, zoneName, reportType for polygon zones
            "attributes": ["waterLevel", "location", "status", "alertThreshold", "district", "waterTrend", "zoneId", "zoneName", "reportType"]
        },
        {
            "id": "urn:ngsi-ld:Subscription:CrowdReport-Storage",
            "name": "CrowdReport → Storage",
            "entity_type": "CrowdReport",
            "attributes": [
                "reporterId", "description", "photos", "timestamp", "waterLevel",
                "verified", "location", "address"
            ]
        },
        {
            "id": "urn:ngsi-ld:Subscription:CameraStream-Storage",
            "name": "CameraStream → Storage",
            "entity_type": "CameraStream",
            "attributes": ["streamUrl", "location", "confidence", "lastUpdate", "monitors", "generates"]
        },
        # Processed/derived entities
        {
            "id": "urn:ngsi-ld:Subscription:FloodRiskSensor-Storage",
            "name": "FloodRiskSensor → Storage",
            "entity_type": "FloodRiskSensor",
            # ✅ FIX: Added zoneId, zoneName, waterTrend for polygon zones
            "attributes": [
                "severity", "alert", "waterLevel", "confidence",
                "sourceSensor", "location", "updatedAt", "district", "sensorInstanceId",
                "zoneId", "zoneName", "waterTrend"
            ]
        },
        {
            "id": "urn:ngsi-ld:Subscription:FloodRiskCrowd-Storage",
            "name": "FloodRiskCrowd → Storage",
            "entity_type": "FloodRiskCrowd",
            "attributes": [
                "riskScore", "riskLevel", "waterLevel", "location",
                "calculatedAt", "factors", "address", "crowdConfidence"
            ]
        },
        {
            "id": "urn:ngsi-ld:Subscription:WeatherObserved-Storage",
            "name": "WeatherObserved → Storage",
            "entity_type": "WeatherObserved",
            "attributes": ["temperature", "humidity", "pressure", "windSpeed", "rainLevel", "dateObserved", "location"]
        },
        {
            "id": "urn:ngsi-ld:Subscription:FloodRiskRain-Storage",
            "name": "FloodRiskRain → Storage",
            "entity_type": "FloodRiskRain",
            "attributes": ["riskScore", "dateObserved", "location"]
        }
    ]

    success = 0
    for sub in subscriptions:
        payload = {
            "id": sub["id"],
            "type": "Subscription",
            "status": "active",
            "entities": [{"type": sub["entity_type"]}],
            "notification": {
                "endpoint": {
                    "uri": QL_NOTIFY_URL,
                    "accept": "application/ld+json"
                },
                "attributes": sub["attributes"]
            },
            "watchedAttributes": sub["attributes"],
            "name": sub["name"],
            "@context": CONTEXT
        }
        
        if create_subscription(payload, sub["name"]):
            success += 1
    
    print(f"  Storage subscriptions: {success}/{len(subscriptions)} created")
    return success

def verify_subscriptions():
    """Verify all subscriptions are active."""
    print("\n🔍 Verifying subscriptions...")
    
    existing = list_subscriptions()
    print(f"  Total active subscriptions: {len(existing)}")
    
    for sub in existing:
        sub_id = sub.get("id", "Unknown")
        status = sub.get("status", "Unknown")
        entities = sub.get("entities", [])
        entity_type = entities[0].get("type") if entities else "Unknown"
        
        icon = "✅" if status == "active" else "⚠"
        print(f"  {icon} {sub_id}")
        print(f"     Type: {entity_type} | Status: {status}")

def main():
    """Main entry point."""
    print("=" * 60)
    print("FloodWatch Subscription Manager v2.0")
    print("=" * 60)
    print(f"Orion-LD: {ORION_URL}")
    print(f"QuantumLeap: {QL_NOTIFY_URL}")
    print(f"FloodWatch API: {API_BASE_URL}")
    
    # Wait for Orion to be ready
    print("\n⏳ Waiting for Orion-LD to be ready...")
    for i in range(30):
        try:
            res = requests.get(f"http://{ORION_HOST}:1026/version", timeout=5)
            if res.status_code == 200:
                print("✔ Orion-LD is ready!")
                break
        except:
            pass
        time.sleep(2)
    else:
        print("⚠ Timeout waiting for Orion-LD, proceeding anyway...")
    
    # Step 1: Cleanup old subscriptions
    cleanup_old_subscriptions()
    
    # Step 2: Register processing subscriptions (FastAPI)
    register_processing_subscriptions()
    
    # Step 3: Register storage subscriptions (QuantumLeap)
    register_storage_subscriptions()
    
    # Step 4: Verify
    verify_subscriptions()
    
    print("\n" + "=" * 60)
    print("✅ Subscription setup complete!")
    print("=" * 60)

# Legacy functions for backward compatibility
def register_subscriptions_fastapi():
    """Legacy wrapper."""
    return register_processing_subscriptions()

def register_subscriptions_ql():
    """Legacy wrapper."""
    return register_storage_subscriptions()

if __name__ == "__main__":
    main()
