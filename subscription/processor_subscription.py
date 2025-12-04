import requests
import json

ORION_SUBSCRIPTIONS = "http://localhost:1026/ngsi-ld/v1/subscriptions"
NGSI_CONTEXT = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"

SUBSCRIPTIONS = [
    {
        "id": "urn:ngsi-ld:Subscription:WaterLevelObserved",
        "entity_type": "WaterLevelObserved",
        "endpoint": "http://localhost:8000/flood/sensor",
        "attributes": [
            "waterLevel",
            "location",
            "alertThreshold",
            "status"
        ]
    },
    {
        "id": "urn:ngsi-ld:Subscription:CrowdReport",
        "entity_type": "CrowdReport",
        "endpoint": "http://localhost:8000/flood/crowd",
        "attributes": [
            "description",
            "verified",
            "location",
            "timestamp"
        ]
    }
]


def register_subscription(sub):
    payload = {
        "id": sub["id"],
        "type": "Subscription",
        "entities": [{"type": sub["entity_type"]}],
        "watchedAttributes": sub["attributes"],     # <--- BẮT BUỘC
        "notification": {
            "attributes": sub["attributes"],
            "format": "normalized",
            "endpoint": {
                "uri": sub["endpoint"],
                "accept": "application/ld+json"
            }
        },
        "isActive": True,
        "@context": [NGSI_CONTEXT]
    }

    print(f"Registering subscription for {sub['entity_type']} ...")

    resp = requests.post(     # <--- Dùng POST
        ORION_SUBSCRIPTIONS,
        json=payload,
        headers={"Content-Type": "application/ld+json"}
    )

    print(f"→ Status {resp.status_code}")
    if resp.status_code >= 300:
        print("Error:", resp.text)


if __name__ == "__main__":
    print("📡 Registering Orion-LD subscriptions...\n")
    for sub in SUBSCRIPTIONS:
        register_subscription(sub)
    print("\n🔥 All subscriptions registered successfully.")
