import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Request, Depends
import json
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

from .services.storage import save_files_local
from .services.orion_client import create_crowd_report_entity
from .schemas import CreateReportResult
from .utils.security import limiter, is_duplicate_image, extract_gps_metadata

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
CORS_ORIGINS = os.getenv("CORS_ORIGINS").split(",")

app = FastAPI()

# Rate limiting configuration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.post("/report", response_model=CreateReportResult)
@limiter.limit("5/minute")  # 5 requests per minute per IP
async def report(
    request: Request,  # Required for rate limiting
    description: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    location_id: Optional[str] = Form(None),
    observation_id: Optional[str] = Form(None),
    water_height: Optional[float] = Form(None),
    images: List[UploadFile] = File([])
):

    try:
        print("\n=== RECEIVED FORM DATA ===")
        print(f"Description: {description}")
        print(f"Latitude: {latitude}")
        print(f"Longitude: {longitude}")
        print(f"Water Height: {water_height}")
        print(f"Number of images: {len(images) if images else 0}")

        # Process images
        processed_images = []
        for img in images:
            img_data = await img.read()
            
            # Check for duplicate images
            if is_duplicate_image(img_data):
                continue  # Skip duplicate images
            # Extract GPS metadata if no coordinates provided
            if latitude is None or longitude is None:
                gps_data = extract_gps_metadata(img_data)
                if gps_data:
                    image_lat = gps_data.get('latitude', latitude)
                    image_long = gps_data.get('longitude', longitude)
                    if latitude !=  image_lat and longitude != image_long:
                        raise HTTPException(
                            status_code=400,
                            detail="Image GPS coordinates do not match provided coordinates"
                        )
            # Reset file pointer after reading
            await img.seek(0)
            processed_images.append(img)

        if not processed_images:
            raise HTTPException(
                status_code=400,
                detail="No valid images provided or all images are duplicates"
            )

        entity_id = create_crowd_report_entity(
            description=description,
            file_uploads=processed_images,
            lat=latitude,
            lng=longitude,
            location_id=location_id,
            observation_id=observation_id,
            water_height=water_height
        )
        
        return {"id": entity_id, "status": "success"}
        
    except Exception as e:
        import traceback
        error_details = {
            "error": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        print("\n=== ERROR DETAILS ===")
        print(json.dumps(error_details, indent=2))
        raise HTTPException(status_code=500, detail={"error": "Failed to create report", "details": str(e)})

@app.get("/")
def root():
    return {"message": "CrowdReport API OK"}