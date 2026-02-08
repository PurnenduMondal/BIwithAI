from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class WidgetBase(BaseModel):
    """Base widget schema"""
    widget_type: str = Field(
        ...,
        pattern="^(chart|metric|table|text|ai_insight)$",
        description="Type of widget"
    )
    title: str = Field(..., min_length=1, max_length=255, description="Widget title")
    position: Dict[str, Any] = Field(
        ...,
        description="Widget position and size {x, y, w, h}"
    )
    config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Widget configuration (chart settings, queries, etc.)"
    )
    data_source_id: Optional[UUID] = Field(None, description="Associated data source")


class WidgetCreate(WidgetBase):
    """Schema for creating a widget"""
    pass


class WidgetUpdate(BaseModel):
    """Schema for updating a widget"""
    widget_type: Optional[str] = Field(None, pattern="^(chart|metric|table|text|ai_insight)$")
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    position: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    data_source_id: Optional[UUID] = None


class WidgetResponse(WidgetBase):
    """Schema for widget response"""
    id: UUID
    dashboard_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WidgetDataResponse(BaseModel):
    """Schema for widget data response"""
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Data rows")
    columns: List[str] = Field(default_factory=list, description="Column names")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata (row count, aggregations, etc.)"
    )

    class Config:
        from_attributes = True
