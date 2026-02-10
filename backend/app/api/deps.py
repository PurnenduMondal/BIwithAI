from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.db.session import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.organization import Organization, OrganizationMember

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = decode_token(token)
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Verify token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current admin user"""
    from app.models.user import UserRole
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_user_organization(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Organization:
    """
    Get user's organization based on:
    1. Subdomain from request (if provided via X-Organization-Subdomain header or Host)
    2. Fallback to user's first organization membership
    
    Verifies that the user is actually a member of the resolved organization.
    """
    org = None
    subdomain = getattr(request.state, "subdomain", None)
    
    # If subdomain is provided, try to resolve organization by subdomain
    if subdomain:
        result = await db.execute(
            select(Organization)
            .join(OrganizationMember)
            .where(Organization.subdomain == subdomain)
            .where(OrganizationMember.user_id == current_user.id)
            .where(Organization.deleted_at.is_(None))
        )
        org = result.scalar_one_or_none()
        
        if not org:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User is not a member of organization with subdomain '{subdomain}'"
            )
    
    # Fallback: get user's first organization if no subdomain specified
    if not org:
        result = await db.execute(
            select(Organization)
            .join(OrganizationMember)
            .where(OrganizationMember.user_id == current_user.id)
            .where(Organization.deleted_at.is_(None))
            .limit(1)
        )
        org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found. User is not a member of any organization."
        )
    
    return org