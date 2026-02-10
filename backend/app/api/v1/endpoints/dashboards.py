from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID
from datetime import timezone

from app.db.session import get_db
from app.api.deps import get_current_user, get_user_organization
from app.schemas.dashboard import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardWithWidgets,
    DashboardGenerateRequest
)
from app.models.user import User
from app.models.organization import Organization
from app.models.dashboard import Dashboard
from app.models.widget import Widget
from app.models.data_source import DataSource
from app.core.security import generate_share_token
from app.workers.dashboard_generation import generate_dashboard_task

router = APIRouter()

@router.get("/", response_model=List[DashboardWithWidgets])
async def list_dashboards(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """List all dashboards for the organization"""
    result = await db.execute(
        select(Dashboard)
        .options(selectinload(Dashboard.widgets))
        .where(Dashboard.org_id == organization.id)
        .where(Dashboard.deleted_at.is_(None))
        .offset(skip)
        .limit(limit)
        .order_by(Dashboard.created_at.desc())
    )
    dashboards = result.scalars().all()
    
    # Filter out soft-deleted widgets
    for dashboard in dashboards:
        if dashboard.widgets:
            dashboard.widgets = [w for w in dashboard.widgets if w.deleted_at is None]
    
    return dashboards

@router.post("/", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Create a new dashboard"""
    dashboard = Dashboard(
        org_id=organization.id,
        created_by=current_user.id,
        **dashboard_data.dict()
    )
    
    db.add(dashboard)
    await db.commit()
    await db.refresh(dashboard)
    
    return dashboard

@router.post("/generate", response_model=DashboardResponse)
async def generate_dashboard(
    request: DashboardGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Auto-generate dashboard from data source"""
    # Verify data source exists
    result = await db.execute(
        select(DataSource)
        .where(DataSource.id == request.data_source_id)
        .where(DataSource.org_id == organization.id)
    )
    data_source = result.scalar_one_or_none()
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    # Create placeholder dashboard
    dashboard = Dashboard(
        org_id=organization.id,
        created_by=current_user.id,
        name=f"{data_source.name} Dashboard",
        description="Auto-generated dashboard",
        layout_config={},
        filters=[],
        theme={}
    )
    
    db.add(dashboard)
    await db.commit()
    await db.refresh(dashboard)
    
    # Generate dashboard in background
    background_tasks.add_task(
        generate_dashboard_task,
        str(dashboard.id),
        str(request.data_source_id),
        request.preferences
    )
    
    return dashboard

@router.get("/{dashboard_id}", response_model=DashboardWithWidgets)
async def get_dashboard(
    dashboard_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific dashboard with widgets"""
    result = await db.execute(
        select(Dashboard)
        .options(selectinload(Dashboard.widgets))
        .where(Dashboard.id == dashboard_id)
        .where(Dashboard.org_id == organization.id)
        .where(Dashboard.deleted_at.is_(None))
    )
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # Filter out soft-deleted widgets
    if dashboard.widgets:
        dashboard.widgets = [w for w in dashboard.widgets if w.deleted_at is None]
    
    return dashboard

@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: UUID,
    update_data: DashboardUpdate,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Update a dashboard"""
    result = await db.execute(
        select(Dashboard)
        .where(Dashboard.id == dashboard_id)
        .where(Dashboard.org_id == organization.id)
    )
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(dashboard, field, value)
    
    await db.commit()
    await db.refresh(dashboard)
    
    return dashboard

@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Delete a dashboard (soft delete)"""
    result = await db.execute(
        select(Dashboard)
        .where(Dashboard.id == dashboard_id)
        .where(Dashboard.org_id == organization.id)
    )
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # Soft delete
    from datetime import datetime
    dashboard.deleted_at = datetime.now(timezone.utc)
    dashboard.is_active = False
    
    await db.commit()
    
    return None

@router.post("/{dashboard_id}/duplicate", response_model=DashboardResponse)
async def duplicate_dashboard(
    dashboard_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Duplicate an existing dashboard"""
    result = await db.execute(
        select(Dashboard)
        .options(selectinload(Dashboard.widgets))
        .where(Dashboard.id == dashboard_id)
        .where(Dashboard.org_id == organization.id)
    )
    original = result.scalar_one_or_none()
    
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # Create duplicate
    duplicate = Dashboard(
        org_id=organization.id,
        created_by=current_user.id,
        name=f"{original.name} (Copy)",
        description=original.description,
        layout_config=original.layout_config.copy(),
        filters=original.filters.copy(),
        theme=original.theme.copy()
    )
    
    db.add(duplicate)
    await db.flush()
    
    # Duplicate widgets
    from app.models.widget import Widget
    for widget in original.widgets:
        duplicate_widget = Widget(
            dashboard_id=duplicate.id,
            data_source_id=widget.data_source_id,
            widget_type=widget.widget_type,
            title=widget.title,
            description=widget.description,
            position=widget.position.copy() if widget.position else {},
            query_config=(widget.query_config or {}).copy(),
            chart_config=(widget.chart_config or {}).copy(),
            data_mapping=(widget.data_mapping or {}).copy(),
            generated_by_ai=widget.generated_by_ai,
            generation_prompt=widget.generation_prompt,
            ai_reasoning=widget.ai_reasoning
        )
        db.add(duplicate_widget)
    
    await db.commit()
    await db.refresh(duplicate)
    
    return duplicate

@router.post("/{dashboard_id}/share")
async def share_dashboard(
    dashboard_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Generate a public share link for dashboard"""
    result = await db.execute(
        select(Dashboard)
        .where(Dashboard.id == dashboard_id)
        .where(Dashboard.org_id == organization.id)
    )
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # Generate share token if not exists
    if not dashboard.public_share_token:
        dashboard.public_share_token = generate_share_token()
        dashboard.is_public = True
        await db.commit()
    
    from app.config import settings
    share_url = f"{settings.FRONTEND_URL}/shared/{dashboard.public_share_token}"
    
    return {
        "share_token": dashboard.public_share_token,
        "share_url": share_url,
        "is_public": dashboard.is_public
    }

@router.get("/templates", response_model=List[DashboardResponse])
async def get_dashboard_templates(
    db: AsyncSession = Depends(get_db)
):
    """Get available dashboard templates"""
    result = await db.execute(
        select(Dashboard)
        .where(Dashboard.is_template == True)
        .where(Dashboard.deleted_at.is_(None))
    )
    templates = result.scalars().all()
    
    return templates