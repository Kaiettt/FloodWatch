import requests

# Orion-LD URL
ORION_URL = "http://localhost:1026/ngsi-ld/v1/subscriptions"
# QuantumLeap notification endpoint
QL_NOTIFY_URL = "http://quantumleap:8668/v2/notify"

# Define subscriptions for each entity with all attributes
subscriptions = [
    {
        "name": "sub-CrowdReport",
        "entity_type": "CrowdReport",
        "attributes": [
            "reporterId", "description", "photos", "timestamp",
            "verified", "locatedAt", "contributesTo", "location"
        ]
    },
    {
        "name": "sub-WaterLevelObserved",
        "entity_type": "WaterLevelObserved",  # Correct entity type
        "attributes": [
            "waterLevel", "location", "status", "alertThreshold"
        ]
    },
    {
        "name": "sub-CameraStream",
        "entity_type": "CameraStream",
        "attributes": [
            "streamUrl", "location", "confidence", "lastUpdate", "monitors", "generates"
        ]
    },
    {
        "name": "sub-FloodRisk",
        "entity_type": "FloodRisk",
        "attributes": [
            "riskLevel", "score", "timestamp", "relatedTo", "locatedAt"
        ]
    }
]

# Create subscriptions
for sub in subscriptions:
    payload = {
        "type": "Subscription",
        "entities": [{"type": sub["entity_type"]}],
        "notification": {
            "endpoint": {
                "uri": QL_NOTIFY_URL,
                "accept": "application/ld+json"
            },
            "attributes": sub["attributes"],
            "format": "normalized"
        },
        "isActive": True,
        "name": sub["name"]
    }

    response = requests.post(ORION_URL, json=payload)
    
    if response.status_code in [201, 200]:
        print(f"Subscription created: {sub['name']}")
    else:
        print(f"Failed to create subscription {sub['name']}: {response.status_code}, {response.text}")
