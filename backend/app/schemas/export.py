from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class ExportFormat(str, Enum):
    PDF = "pdf"
    PNG = "png"
    SVG = "svg"
    JSON = "json"
    XLSX = "xlsx"

class ExportJobResponse(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: Optional[int] = 0  # 0-100
    message: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_time: Optional[int] = None  # seconds