from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timezone

from app.db.session import get_db
from app.api.deps import get_current_user
from app.schemas.user import UserResponse, UserUpdate
from app.models.user import User
from app.core.security import get_password_hash, verify_password

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

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