from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class InsightGenerateRequest(BaseModel):
    """Request schema for generating insights"""
    context: Optional[str] = Field(
        None,
        description="Additional context to guide insight generation"
    )


class InsightBase(BaseModel):
    """Base insight schema"""
    insight_type: str = Field(..., description="Type of insight (trend, anomaly, correlation, etc.)")
    content: str = Field(..., description="Human-readable insight description")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    insight_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional insight metadata")


class InsightCreate(InsightBase):
    """Schema for creating an insight"""
    dashboard_id: UUID


class InsightResponse(InsightBase):
    """Schema for insight response"""
    id: UUID
    dashboard_id: UUID
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
