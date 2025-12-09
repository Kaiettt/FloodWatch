# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

from pydantic import BaseModel, Field
from typing import List, Optional, Union, Any, Dict

class CreateReportResult(BaseModel):
    id: str
    status: str
    image_urls: Optional[List[str]] = None
    waterLevel: Optional[float] = Field(
        None,
        alias="water_level",
        description="Water level in meters",
        ge=0,
        le=20  # Max 20m water level
    )
    
    class Config:
        populate_by_name = True

# ✅ NEW: Pydantic models for NGSI-LD validation
class NGSILDProperty(BaseModel):
    type: str = "Property"
    value: Any
    observedAt: Optional[str] = None
    unitCode: Optional[str] = None

class NGSILDGeoProperty(BaseModel):
    type: str = "GeoProperty"
    value: Dict[str, Any]

class WaterLevelObservedData(BaseModel):
    """Validated sensor data structure."""
    id: str
    type: str = "WaterLevelObserved"
    waterLevel: NGSILDProperty
    location: NGSILDGeoProperty
    alertThreshold: Optional[NGSILDProperty] = None
    district: Optional[NGSILDProperty] = None
    waterTrend: Optional[NGSILDProperty] = None

class FloodNearbyRequest(BaseModel):
    """Request for nearby floods."""
    lat: float = Field(..., ge=8.5, le=23.4, description="Latitude (Vietnam)")
    lng: float = Field(..., ge=102.1, le=109.5, description="Longitude (Vietnam)")
    radius_km: float = Field(5.0, ge=0.1, le=100, description="Radius in km")
    limit: int = Field(100, ge=1, le=500, description="Max results")

class RiskScoreFactors(BaseModel):
    """Breakdown of risk score calculation."""
    waterLevelFactor: float
    textSeverityFactor: float
    photoFactor: float
    verifiedFactor: float
    keywordMatches: Optional[int] = None

class DashboardStats(BaseModel):
    """Dashboard statistics response."""
    total: int
    severe: int
    high: int
    medium: int
    low: int
    avgWaterLevel: float
    sensorCount: int
    communityCount: int
    lastUpdated: str
    filter: Optional[Dict[str, Any]] = None
