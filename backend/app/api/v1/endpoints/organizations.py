from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID
from datetime import datetime, timezone

from app.db.session import get_db
from app.api.deps import get_current_user, get_current_admin_user
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationMemberResponse,
    OrganizationMemberCreate
)
from app.models.user import User
from app.models.organization import Organization, OrganizationMember

router = APIRouter()

@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all organizations user belongs to"""
    result = await db.execute(
        select(Organization)
        .join(OrganizationMember)
        .where(OrganizationMember.user_id == current_user.id)
        .where(Organization.deleted_at.is_(None))
    )
    organizations = result.scalars().all()
    
    return organizations

@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new organization"""
    # Check if subdomain is already taken
    if org_data.subdomain:
        existing = await db.execute(
            select(Organization).where(Organization.subdomain == org_data.subdomain)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subdomain already taken"
            )
    
    # Create organization
    organization = Organization(**org_data.dict())
    db.add(organization)
    await db.flush()
    
    # Add creator as admin member
    member = OrganizationMember(
        org_id=organization.id,
        user_id=current_user.id,
        role="admin"
    )
    db.add(member)
    
    await db.commit()
    await db.refresh(organization)
    
    return organization

@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get organization details"""
    # Verify user is member
    member_check = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.org_id == org_id)
        .where(OrganizationMember.user_id == current_user.id)
    )
    if not member_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )
    
    result = await db.execute(
        select(Organization)
        .where(Organization.id == org_id)
        .where(Organization.deleted_at.is_(None))
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return organization

@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    update_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update organization (admin only)"""
    # Verify user is admin
    member_check = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.org_id == org_id)
        .where(OrganizationMember.user_id == current_user.id)
        .where(OrganizationMember.role == "admin")
    )
    if not member_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check subdomain uniqueness if changing
    if update_data.subdomain and update_data.subdomain != organization.subdomain:
        existing = await db.execute(
            select(Organization).where(Organization.subdomain == update_data.subdomain)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subdomain already taken"
            )
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(organization, field, value)
    
    await db.commit()
    await db.refresh(organization)
    
    return organization

@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete organization (admin only, soft delete)"""
    # Verify user is admin
    member_check = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.org_id == org_id)
        .where(OrganizationMember.user_id == current_user.id)
        .where(OrganizationMember.role == "admin")
    )
    if not member_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    organization.deleted_at = datetime.now(timezone.utc)
    organization.is_active = False
    
    await db.commit()
    
    return None

@router.get("/{org_id}/members", response_model=List[OrganizationMemberResponse])
async def list_organization_members(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List organization members"""
    # Verify user is member
    member_check = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.org_id == org_id)
        .where(OrganizationMember.user_id == current_user.id)
    )
    if not member_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )
    
    result = await db.execute(
        select(OrganizationMember)
        .options(selectinload(OrganizationMember.user))
        .where(OrganizationMember.org_id == org_id)
        .where(OrganizationMember.deleted_at.is_(None))
    )
    members = result.scalars().all()
    
    return members

@router.post("/{org_id}/members", response_model=OrganizationMemberResponse)
async def add_organization_member(
    org_id: UUID,
    member_data: OrganizationMemberCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add member to organization (admin only)"""
    # Verify user is admin
    admin_check = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.org_id == org_id)
        .where(OrganizationMember.user_id == current_user.id)
        .where(OrganizationMember.role == "admin")
    )
    if not admin_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Check if user exists
    user_result = await db.execute(
        select(User).where(User.id == member_data.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already a member
    existing = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.org_id == org_id)
        .where(OrganizationMember.user_id == member_data.user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member"
        )
    
    # Add member
    member = OrganizationMember(
        org_id=org_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    db.add(member)
    await db.commit()
    
    # Reload with user relationship
    result = await db.execute(
        select(OrganizationMember)
        .options(selectinload(OrganizationMember.user))
        .where(OrganizationMember.id == member.id)
    )
    member = result.scalar_one()
    
    return member

@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    org_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove member from organization (admin only)"""
    # Verify user is admin
    admin_check = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.org_id == org_id)
        .where(OrganizationMember.user_id == current_user.id)
        .where(OrganizationMember.role == "admin")
    )
    if not admin_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get member
    result = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.org_id == org_id)
        .where(OrganizationMember.user_id == user_id)
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Don't allow removing the last admin
    if member.role == "admin":
        admin_count = await db.execute(
            select(OrganizationMember)
            .where(OrganizationMember.org_id == org_id)
            .where(OrganizationMember.role == "admin")
        )
        if len(admin_count.scalars().all()) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last admin"
            )
    
    member.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    
    return None