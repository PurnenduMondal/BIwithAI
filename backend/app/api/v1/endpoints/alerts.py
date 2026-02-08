from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone

from app.db.session import get_db
from app.api.deps import get_current_user, get_user_organization
from app.schemas.alert import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertWithHistory,
    AlertHistoryResponse
)
from app.models.user import User
from app.models.organization import Organization
from app.models.alert import Alert, AlertHistory
from app.models.dashboard import Dashboard
from app.models.widget import Widget

router = APIRouter()

ALERT_NOT_FOUND_DETAIL = "Alert not found"

@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    dashboard_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """List all alerts for the organization"""
    query = select(Alert).join(Dashboard).where(
        Dashboard.org_id == organization.id,
        Alert.deleted_at.is_(None)
    )
    
    if is_active is not None:
        query = query.where(Alert.is_active == is_active)
    
    if dashboard_id:
        query = query.where(Alert.dashboard_id == dashboard_id)
    
    query = query.offset(skip).limit(limit).order_by(Alert.created_at.desc())
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return alerts

@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Create a new alert"""
    # Verify dashboard belongs to organization
    dashboard_result = await db.execute(
        select(Dashboard).where(
            Dashboard.id == alert_data.dashboard_id,
            Dashboard.org_id == organization.id
        )
    )
    dashboard = dashboard_result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # If widget_id provided, verify it belongs to the dashboard
    if alert_data.widget_id:
        widget_result = await db.execute(
            select(Widget).where(
                Widget.id == alert_data.widget_id,
                Widget.dashboard_id == alert_data.dashboard_id
            )
        )
        widget = widget_result.scalar_one_or_none()
        
        if not widget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Widget not found in specified dashboard"
            )
    
    # Create alert
    alert = Alert(
        dashboard_id=alert_data.dashboard_id,
        widget_id=alert_data.widget_id,
        condition=alert_data.condition,
        notification_channels=alert_data.notification_channels,
        is_active=alert_data.is_active
    )
    
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    
    return alert

@router.get("/{alert_id}", response_model=AlertWithHistory)
async def get_alert(
    alert_id: UUID,
    include_history: bool = Query(True),
    history_limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific alert with optional history"""
    # Get alert
    alert_result = await db.execute(
        select(Alert)
        .join(Dashboard)
        .where(
            Alert.id == alert_id,
            Dashboard.org_id == organization.id,
            Alert.deleted_at.is_(None)
        )
    )
    alert = alert_result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ALERT_NOT_FOUND_DETAIL
        )
    
    response_data = alert.to_dict()
    
    # Get history if requested
    if include_history:
        history_result = await db.execute(
            select(AlertHistory)
            .where(AlertHistory.alert_id == alert_id)
            .order_by(AlertHistory.triggered_at.desc())
            .limit(history_limit)
        )
        history = history_result.scalars().all()
        
        response_data['history'] = [h.to_dict() for h in history]
        response_data['total_triggers'] = len(history)
    
    return response_data

@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: UUID,
    update_data: AlertUpdate,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Update an alert"""
    # Get alert
    alert_result = await db.execute(
        select(Alert)
        .join(Dashboard)
        .where(
            Alert.id == alert_id,
            Dashboard.org_id == organization.id
        )
    )
    alert = alert_result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ALERT_NOT_FOUND_DETAIL
        )
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(alert, field, value)
    
    await db.commit()
    await db.refresh(alert)
    
    return alert

@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Delete an alert (soft delete)"""
    # Get alert
    alert_result = await db.execute(
        select(Alert)
        .join(Dashboard)
        .where(
            Alert.id == alert_id,
            Dashboard.org_id == organization.id
        )
    )
    alert = alert_result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ALERT_NOT_FOUND_DETAIL
        )
    
    # Soft delete
    alert.deleted_at = datetime.now(timezone.utc)
    alert.is_active = False
    
    await db.commit()
    
    return None

@router.get("/history", response_model=List[AlertHistoryResponse])
async def get_alerts_history(
    skip: int = 0,
    limit: int = 100,
    alert_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get alert trigger history"""
    query = (
        select(AlertHistory)
        .join(Alert)
        .join(Dashboard)
        .where(Dashboard.org_id == organization.id)
    )
    
    if alert_id:
        query = query.where(AlertHistory.alert_id == alert_id)
    
    if start_date:
        query = query.where(AlertHistory.triggered_at >= start_date)
    
    if end_date:
        query = query.where(AlertHistory.triggered_at <= end_date)
    
    query = query.offset(skip).limit(limit).order_by(AlertHistory.triggered_at.desc())
    
    result = await db.execute(query)
    history = result.scalars().all()
    
    return history