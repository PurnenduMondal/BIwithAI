from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.schemas.user import UserResponse


class OrganizationBase(BaseModel):
    """Base organization schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    subdomain: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100,
        pattern="^[a-z0-9-]+$",
        description="Unique subdomain (lowercase alphanumeric and hyphens only)"
    )
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Organization settings")


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization"""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    subdomain: Optional[str] = Field(None, min_length=3, max_length=100, pattern="^[a-z0-9-]+$")
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    """Schema for organization response"""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrganizationMemberBase(BaseModel):
    """Base organization member schema"""
    role: str = Field(..., pattern="^(admin|member|viewer)$", description="Member role")


class OrganizationMemberCreate(OrganizationMemberBase):
    """Schema for adding a member to an organization"""
    user_id: UUID


class OrganizationMemberResponse(OrganizationMemberBase):
    """Schema for organization member response"""
    id: UUID
    org_id: UUID
    user_id: UUID
    user: Optional[UserResponse] = None
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
