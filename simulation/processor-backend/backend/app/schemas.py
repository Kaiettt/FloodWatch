from pydantic import BaseModel, Field
from typing import List, Optional, Union

class CreateReportResult(BaseModel):
    id: str
    status: str
    image_urls: Optional[List[str]] = None
    water_level: Optional[float] = Field(
        None,
        description="Water level in meters",
        ge=0,
        le=1000  # Reasonable upper limit for water level in meters
    )
