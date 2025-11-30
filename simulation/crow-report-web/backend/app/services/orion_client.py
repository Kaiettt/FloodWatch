import os
import uuid
import datetime
import requests
from typing import List, Optional
import json

# --- Config ---
ORION_LD_URL = os.getenv("ORION_LD_URL", "http://localhost:1026/ngsi-ld/v1/entities")

HEADERS = {
    "Content-Type": "application/ld+json"  # Chỉ cần thế này thôi
}

# --- Build payload ---
def build_crowd_report_sdm(
    description: str,
    reporterId: str,
    photo_urls: Optional[List[str]] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    location_id: Optional[str] = None,
    observation_id: Optional[str] = None
) -> dict:
    """
    Build CrowdReport entity in NGSI-LD Smart Data Model format
    """
    entity_id = f"urn:ngsi-ld:CrowdReport:{uuid.uuid4().hex}"
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    payload = {
        "id": entity_id,
        "type": "CrowdReport",
        "reporterId": {"type": "Property", "value": reporterId},
        "description": {"type": "Property", "value": description},
        "photos": {"type": "Property", "value": photo_urls or []},
        "timestamp": {"type": "Property", "value": timestamp},
        "verified": {"type": "Property", "value": False},
         "@context": ["https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"]
    }

    if lat is not None and lng is not None:
        payload["location"] = {
            "type": "GeoProperty",
            "value": {"type": "Point", "coordinates": [lng, lat]}
        }

    if location_id:
        payload["locatedAt"] = {"type": "Relationship", "object": location_id}
    if observation_id:
        payload["contributesTo"] = {"type": "Relationship", "object": observation_id}

    return payload

# --- Send to Orion-LD ---
def create_crowd_report_entity(
    description: str,
    reporterId: str,
    photo_urls: Optional[List[str]] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    location_id: Optional[str] = None,
    observation_id: Optional[str] = None
) -> str:
    """
    Create a CrowdReport entity in Orion-LD
    """
    payload = build_crowd_report_sdm(description, reporterId, photo_urls, lat, lng, location_id, observation_id)

    # Debug print
    print("\n=== PAYLOAD SENT TO ORION-LD ===")
    print(json.dumps(payload, indent=4, ensure_ascii=False))

    # Send POST request
    resp = requests.post(ORION_LD_URL, json=payload, headers=HEADERS)

    print("\n=== ORION-LD RESPONSE ===")
    print("Status:", resp.status_code)
    try:
        print(json.dumps(resp.json(), indent=4, ensure_ascii=False))
    except Exception:
        print(resp.text)

    if not resp.ok:
        raise Exception(f"Failed to create entity: {resp.text}")

    return payload["id"]

# --- Example usage ---
if __name__ == "__main__":
    try:
        entity_id = create_crowd_report_entity(
            description="Ngập trên đường Nguyễn Huệ, khoảng 20cm",
            reporterId="user123",
            photo_urls=["http://localhost:8000/static/uploads/example.png"],
            lat=21.0245,
            lng=105.84117
        )
        print(f"\n✅ CrowdReport created with ID: {entity_id}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
