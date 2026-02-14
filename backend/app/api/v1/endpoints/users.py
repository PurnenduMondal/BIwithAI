from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, timezone

from app.db.session import get_db
from app.api.deps import get_current_user
from app.schemas.user import UserResponse, UserUpdate, OrganizationMembership
from app.models.user import User
from app.models.organization import OrganizationMember, Organization
from app.core.security import get_password_hash, verify_password

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user information with organization memberships"""
    # Load user's organization memberships
    result = await db.execute(
        select(OrganizationMember, Organization)
        .join(Organization, OrganizationMember.org_id == Organization.id)
        .where(OrganizationMember.user_id == current_user.id)
        .where(Organization.is_active == True)
    )
    
    memberships = []
    for member, org in result.all():
        memberships.append(OrganizationMembership(
            org_id=org.id,
            org_name=org.name,
            subdomain=org.subdomain,
            role=member.role
        ))
    
    # Create response with organizations
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login,
        "organizations": memberships
    }
    
    return UserResponse(**user_dict)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user information"""
    update_data = user_update.dict(exclude_unset=True)
    
    # If password is being updated, hash it
    if 'password' in update_data:
        update_data['password_hash'] = get_password_hash(update_data.pop('password'))
    
    # Update user fields
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete current user account (soft delete)"""
    current_user.deleted_at = datetime.now(timezone.utc)
    current_user.is_active = False
    
    await db.commit()
    
    return None

@router.get("/me/preferences")
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user preferences"""
    # Store preferences in a separate table or in user JSONB field
    # For now, return empty preferences
    return {
        "theme": "light",
        "language": "en",
        "timezone": "UTC",
        "notifications": {
            "email": True,
            "push": False
        },
        "dashboard_defaults": {
            "refresh_interval": 300,
            "default_date_range": "last_30_days"
        }
    }

@router.put("/me/preferences")
async def update_user_preferences(
    preferences: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user preferences"""
    # In production, store in separate preferences table or JSONB field
    # For now, just return the preferences
    return preferences