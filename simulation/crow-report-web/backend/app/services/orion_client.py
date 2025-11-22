import os
import uuid
import datetime
import requests
from typing import List, Optional
import json
from fastapi import  UploadFile
from .ai_verify import detect_flood_and_objects
# --- Config ---
ORION_LD_URL = os.getenv("ORION_LD_URL", "http://localhost:1026/ngsi-ld/v1/entities")

HEADERS = {
    "Content-Type": "application/ld+json"  # Chỉ cần thế này thôi
}

# --- Build payload ---
def build_crowd_report_sdm(
    description: str,
    water_height: Optional[float] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    location_id: Optional[str] = None,
    observation_id: Optional[str] = None,
    photos: Optional[List[str]] = None
) -> dict:
    """
    Build CrowdReport entity in NGSI-LD Smart Data Model format
    """
    entity_id = f"urn:ngsi-ld:CrowdReport:{uuid.uuid4().hex}"
    reporter_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    payload = {
        "id": entity_id,
        "type": "CrowdReport",
        "reporterId": {
            "type": "Property",
            "value": reporter_id
        },
        "description": {
            "type": "Property",
            "value": description
        },
        "timestamp": {
            "type": "Property",
            "value": timestamp
        },
        "@context": [
            "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
        ]
    }


    if lat is not None and lng is not None:
        payload["location"] = {
            "type": "GeoProperty",
            "value": {
                "type": "Point",
                "coordinates": [lng, lat]
            }
        }

    if location_id:
        payload["locatedAt"] = {
            "type": "Relationship",
            "object": location_id
        }
    if observation_id:
        payload["contributesTo"] = {
            "type": "Relationship",
            "object": observation_id
        }
    if water_height is not None:
        payload["waterHeight"] = {
            "type": "Property",
            "value": water_height,
            "unitCode": "MTR"
        }
        
    if photos:
        payload["photos"] = {
            "type": "Property",
            "value": photos
        }
    return payload

# --- Send to Orion-LD ---
def create_crowd_report_entity(
    description: str,
    file_uploads: List[UploadFile] = None,
    water_height: Optional[float] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    location_id: Optional[str] = None,
    observation_id: Optional[str] = None
) -> str:
    """
    Create a CrowdReport entity in Orion-LD
    """

    photo_urls = []
    for file_upload in file_uploads:
        if file_upload.filename:
            # Verify if the file is a flood image
            if detect_flood_and_objects(file_upload.file):
                photo_urls.append(file_upload.filename)
            else:
                raise ValueError(f"File {file_upload.filename} is not a flood image")

    payload = build_crowd_report_sdm(
        description=description,
        water_height=water_height,
        lat=lat,
        lng=lng,
        location_id=location_id,
        observation_id=observation_id,
        photos=photo_urls
    )

    # Debug print
    print("\n=== PAYLOAD SENT TO ORION-LD ===")
    print(json.dumps(payload, indent=4, ensure_ascii=False))
    print("\n=== SENDING TO URL ===")
    print(f"URL: {ORION_LD_URL}")
    print(f"HEADERS: {json.dumps(HEADERS, indent=4)}")

    try:
        # Send POST request with timeout
        resp = requests.post(
            ORION_LD_URL,
            json=payload,
            headers=HEADERS,
            timeout=10  # 10 seconds timeout
        )
        
        print("\n=== ORION-LD RESPONSE ===")
        print(f"Status Code: {resp.status_code}")
        print("Headers:", dict(resp.headers))
        
        try:
            response_data = resp.json()
            print("Response JSON:", json.dumps(response_data, indent=4, ensure_ascii=False))
        except ValueError:
            print("Response Text:", resp.text[:1000])  # Print first 1000 chars if not JSON

        resp.raise_for_status()  # This will raise an HTTPError for bad status codes
        
    except requests.exceptions.RequestException as e:
        print("\n=== REQUEST ERROR ===")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print("Response Headers:", dict(e.response.headers))
            try:
                print("Response Body:", e.response.json())
            except ValueError:
                print("Response Text:", e.response.text[:1000])
        raise Exception(f"Failed to create entity: {str(e)}") from e

    return payload["id"]

# --- Example usage ---
if __name__ == "__main__":
    try:
        entity_id = create_crowd_report_entity(
            description="Flooding on Main Street",
            water_height=0.5,  # Example water height in meters
            lat=10.1234,
            lng=106.5678,
            file_uploads=None,  # In the example, we're not uploading files
        )
        print(f"\n✅ CrowdReport created with ID: {entity_id}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
