import requests

# Orion-LD endpoint
ORION_URL = "http://localhost:1026/ngsi-ld/v1/subscriptions"

# QuantumLeap notification endpoint
QL_NOTIFY_URL = "http://quantumleap:8668/v2/notify"

# NGSI-LD core context v1.6 (requested)
CONTEXT = [
    "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.6.jsonld"
]

# Subscriptions definition
subscriptions = [
    {
        "name": "sub-CrowdReport",
        "entity_type": "CrowdReport",
        "attributes": [
            "reporterId", "description", "photos", "timestamp","water_level",
            "verified", "location"
        ]
    },
    {
        "name": "sub-WaterLevelObserved",
        "entity_type": "WaterLevelObserved",
        "attributes": [
            "waterLevel", "location", "status", "alertThreshold"
        ]
    },
    {
        "name": "sub-CameraStream",
        "entity_type": "CameraStream",
        "attributes": [
            "streamUrl", "location", "confidence", "lastUpdate",
            "monitors", "generates"
        ]
    },
    {
        "name": "sub-FloodRiskSensor",
        "entity_type": "FloodRiskSensor",
        "attributes": [
            "severity", "alert", "waterLevel", "confidence",
            "sourceSensor", "location", "updatedAt"
        ]
    },
    {
        "name": "sub-FloodRiskCrowd",
        "entity_type": "FloodRiskCrowd",
        "attributes": [
            "riskScore", "riskLevel", "waterLevel", "location",
            "calculatedAt", "factors"
        ]
    },
    {
        "name": "sub-WeatherObserved",
        "entity_type": "WeatherObserved",
        "attributes": ["temperature", "humidity", "pressure", "windSpeed", "rainLevel", "dateObserved"]
    },
    {
        "name": "sub-FloodRiskRain",
        "entity_type": "FloodRiskRain",
        "attributes": ["riskScore", "dateObserved", "location"]
    }
]

headers = {"Content-Type": "application/ld+json"}

# Create subscriptions
for sub in subscriptions:
    payload = {
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
        "name": sub["name"],
        "@context": CONTEXT
    }

    response = requests.post(ORION_URL, json=payload, headers=headers)

    if response.status_code in [200, 201]:
        print(f"Subscription created: {sub['name']}")
    else:
        print(f"Failed to create subscription {sub['name']}: {response.status_code}")
        print(response.text)
