import os
from typing import List, Optional
from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from .services.storage import save_files_local
from .services.orion_client import create_crowd_report_entity
from .schemas import CreateReportResult
load_dotenv()

BASE_URL = os.getenv("BASE_URL")
CORS_ORIGINS = os.getenv("CORS_ORIGINS").split(",")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.post("/report", response_model=CreateReportResult)
async def report(
    description: str = Form(...),
    reporterId: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    locationId: Optional[str] = Form(None),
    observationId: Optional[str] = Form(None),
    images: List[UploadFile] = File([])
):
    try:
        image_urls = save_files_local(images, BASE_URL)
    except Exception as e:
        raise HTTPException(500, f"Cannot save images: {str(e)}")

    try:
        entity_id = create_crowd_report_entity(
            description=description,
            reporterId=reporterId,
            photo_urls=image_urls,
            lat=latitude,
            lng=longitude,
            location_id=locationId,
            observation_id=observationId
        )
    except Exception as e:
        raise HTTPException(500, f"Orion-LD error: {str(e)}")

    return {"id": entity_id, "status": "created", "image_urls": image_urls}


@app.get("/")
def root():
    return {"message": "CrowdReport API OK"}