import requests

ORION_URL = "http://localhost:1026/ngsi-ld/v1/subscriptions"

# Your required @context
CONTEXT = [
    "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.6.jsonld"
]
SUBSCRIPTIONS = [
    {
        "id": "urn:ngsi-ld:Subscription:WaterLevelObserved",
        "name": "WaterLevelObserved-Subscription",
        "entity_type": "WaterLevelObserved",
        "endpoint": "http://host.docker.internal:8000/flood/sensor",
        "attributes": ["waterLevel", "location", "status", "alertThreshold"]
    },
    {
        "id": "urn:ngsi-ld:Subscription:CrowdReport",
        "name": "CrowdReport-Subscription",
        "entity_type": "CrowdReport",
        "endpoint": "http://host.docker.internal:8000/flood/crowd",
        "attributes": [
            "reporterId", "description", "photos", "timestamp","waterLevel",
            "verified", "location"
        ]
    }
]


def register_subscription(sub):

    # --- YOUR REQUIRED FORMAT EXACTLY AS REQUESTED ---
    payload = {
        "id": sub["id"],
        "type": "Subscription",
        "status": "active",

        "entities": [
            {"type": sub["entity_type"]}
        ],

        "notification": {
            "endpoint": {
                "uri": sub["endpoint"],     # <-- your FastAPI endpoint
                "accept": "application/ld+json"
            },
            "attributes": sub["attributes"]
        },

        "watchedAttributes": sub["attributes"],

        "name": sub["name"],
        "@context": CONTEXT
    }
    # ----------------------------------------------------

    headers = {"Content-Type": "application/ld+json"}

    res = requests.post(ORION_URL, json=payload, headers=headers)

    if res.status_code in (200, 201):
        print(f"✔ Subscription created: {sub['id']}")
    elif res.status_code == 409:
        print(f"⚠ Already exists: {sub['id']}")
    else:
        print(f"❌ Failed ({res.status_code}) → {sub['id']}")
        print(res.text)


if __name__ == "__main__":
    for sub in SUBSCRIPTIONS:
        register_subscription(sub)
