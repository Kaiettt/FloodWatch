from pydantic import BaseModel
from typing import List, Optional

class CreateReportResult(BaseModel):
    id: str
    status: str
    image_urls: Optional[List[str]] = None
