import os
import requests

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

def register_subscriptions_fastapi():
    """Register 2 subscriptions with FastAPI endpoints."""
    subscriptions = [
        {
            "id": "urn:ngsi-ld:Subscription:WaterLevelObserved",
            "name": "WaterLevelObserved-Subscription",
            "entity_type": "WaterLevelObserved",
            "endpoint": f"{API_BASE_URL}/flood/sensor",
            "attributes": ["waterLevel", "location", "status", "alertThreshold","district"]
        },
        {
            "id": "urn:ngsi-ld:Subscription:CrowdReport",
            "name": "CrowdReport-Subscription",
            "entity_type": "CrowdReport",
            "endpoint": f"{API_BASE_URL}/flood/crowd",
            "attributes": [
                "reporterId", "description", "photos", "timestamp", "waterLevel",
                "verified", "location","address"
            ]
        },
        {
            "id": "urn:ngsi-ld:Subscription:WeatherObserved",
            "name": "WeatherObserved-Subscription",
            "entity_type": "WeatherObserved",
            "endpoint": f"{API_BASE_URL}/weather/notify",
            "attributes": ["temperature", "humidity", "pressure", "windSpeed", "rainLevel", "dateObserved"]
        }
    ]

    headers = {"Content-Type": "application/ld+json"}

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

        res = requests.post(ORION_URL, json=payload, headers=headers)
        if res.status_code in (200, 201):
            print(f"✔ Subscription created: {sub['id']}")
        elif res.status_code == 409:
            print(f"⚠ Already exists: {sub['id']}")
        else:
            print(f"❌ Failed ({res.status_code}) → {sub['id']}")
            print(res.text)

def register_subscriptions_ql():
    """Register 5 subscriptions with QuantumLeap notification endpoint."""
    subscriptions = [
        {
            "id": "urn:ngsi-ld:Subscription:WaterLevelObserved-QL",
            "name": "sub-WaterLevelObserved",
            "entity_type": "WaterLevelObserved",
            "attributes": ["waterLevel", "location", "status", "alertThreshold","district"]
        },
        {
            "id": "urn:ngsi-ld:Subscription:CrowdReport-QL",
            "name": "sub-CrowdReport",
            "entity_type": "CrowdReport",
            "attributes": [
                "reporterId", "description", "photos", "timestamp", "water_level",
                "verified", "location","address"
            ]
        },
        {
            "id": "urn:ngsi-ld:Subscription:CameraStream",
            "name": "sub-CameraStream",
            "entity_type": "CameraStream",
            "attributes": ["streamUrl", "location", "confidence", "lastUpdate",
                           "monitors", "generates"]
        },
        {
            "id": "urn:ngsi-ld:Subscription:FloodRiskSensor",
            "name": "sub-FloodRiskSensor",
            "entity_type": "FloodRiskSensor",
            "attributes": ["severity", "alert", "waterLevel", "confidence",
                           "sourceSensor", "location", "updatedAt","district"]
        },
        {
            "id": "urn:ngsi-ld:Subscription:FloodRiskCrowd",
            "name": "sub-FloodRiskCrowd",
            "entity_type": "FloodRiskCrowd",
            "attributes": ["riskScore", "riskLevel", "waterLevel", "location",
                           "calculatedAt", "factors","address"]
        },
        {
            "id": "urn:ngsi-ld:Subscription:WeatherObserved",
            "name": "sub-WeatherObserved",
            "entity_type": "WeatherObserved",
            "attributes": ["temperature", "humidity", "pressure", "windSpeed", "rainLevel", "dateObserved"]
        },
        {
            "id": "urn:ngsi-ld:Subscription:FloodRiskRain",
            "name": "sub-FloodRiskRain",
            "entity_type": "FloodRiskRain",
            "attributes": ["riskScore", "dateObserved", "location"]
        }
    ]

    headers = {"Content-Type": "application/ld+json"}

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

        res = requests.post(ORION_URL, json=payload, headers=headers)
        if res.status_code in (200, 201):
            print(f"✔ Subscription created: {sub['id']}")
        elif res.status_code == 409:
            print(f"⚠ Already exists: {sub['id']}")
        else:
            print(f"❌ Failed ({res.status_code}) → {sub['id']}")
            print(res.text)

if __name__ == "__main__":
    print("Registering FastAPI subscriptions...")
    register_subscriptions_fastapi()

    print("\nRegistering QuantumLeap subscriptions...")
    register_subscriptions_ql()