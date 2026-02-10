from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from .widget import WidgetResponse

class DashboardBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class DashboardCreate(DashboardBase):
    layout_config: Optional[Dict[str, Any]] = {}
    filters: Optional[List[Dict[str, Any]]] = []
    theme: Optional[Dict[str, Any]] = {}

class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    layout_config: Optional[Dict[str, Any]] = None
    filters: Optional[List[Dict[str, Any]]] = None
    theme: Optional[Dict[str, Any]] = None

class DashboardResponse(DashboardBase):
    id: UUID
    org_id: UUID
    created_by: UUID
    layout_config: Dict[str, Any]
    filters: List[Dict[str, Any]]
    theme: Dict[str, Any]
    is_template: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

class DashboardWithWidgets(DashboardResponse):
    widgets: List[WidgetResponse]

class DashboardGenerateRequest(BaseModel):
    data_source_id: UUID
    preferences: Optional[Dict[str, Any]] = {}