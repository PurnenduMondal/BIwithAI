from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
import pandas as pd
from datetime import datetime, timezone

from app.db.session import get_db
from app.api.deps import get_current_user, get_user_organization
from app.schemas.widget import WidgetCreate, WidgetUpdate, WidgetResponse, WidgetDataResponse
from app.models.user import User
from app.models.organization import Organization
from app.models.widget import Widget
from app.models.dashboard import Dashboard
from app.models.data_source import DataSource, Dataset
from app.services.query.query_executor import QueryExecutor

router = APIRouter()

@router.get("/dashboards/{dashboard_id}/widgets", response_model=List[WidgetResponse])
async def list_dashboard_widgets(
    dashboard_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """List all widgets for a dashboard"""
    # Verify dashboard belongs to org
    dashboard_result = await db.execute(
        select(Dashboard)
        .where(Dashboard.id == dashboard_id)
        .where(Dashboard.org_id == organization.id)
    )
    dashboard = dashboard_result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    result = await db.execute(
        select(Widget)
        .where(Widget.dashboard_id == dashboard_id)
        .where(Widget.deleted_at.is_(None))
        .order_by(Widget.created_at)
    )
    widgets = result.scalars().all()
    
    return widgets

@router.post("/dashboards/{dashboard_id}/widgets", response_model=WidgetResponse)
async def create_widget(
    dashboard_id: UUID,
    widget_data: WidgetCreate,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Create a new widget"""
    # Verify dashboard
    dashboard_result = await db.execute(
        select(Dashboard)
        .where(Dashboard.id == dashboard_id)
        .where(Dashboard.org_id == organization.id)
    )
    dashboard = dashboard_result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # Create widget
    widget = Widget(
        dashboard_id=dashboard_id,
        **widget_data.dict()
    )
    
    db.add(widget)
    await db.commit()
    await db.refresh(widget)
    
    return widget

@router.get("/{widget_id}", response_model=WidgetResponse)
async def get_widget(
    widget_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get widget details"""
    result = await db.execute(
        select(Widget)
        .join(Dashboard)
        .where(Widget.id == widget_id)
        .where(Dashboard.org_id == organization.id)
    )
    widget = result.scalar_one_or_none()
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    return widget

@router.put("/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    widget_id: UUID,
    update_data: WidgetUpdate,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Update widget"""
    result = await db.execute(
        select(Widget)
        .join(Dashboard)
        .where(Widget.id == widget_id)
        .where(Dashboard.org_id == organization.id)
    )
    widget = result.scalar_one_or_none()
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(widget, field, value)
    
    await db.commit()
    await db.refresh(widget)
    
    return widget

@router.delete("/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    widget_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Delete widget"""
    result = await db.execute(
        select(Widget)
        .join(Dashboard)
        .where(Widget.id == widget_id)
        .where(Dashboard.org_id == organization.id)
    )
    widget = result.scalar_one_or_none()
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    widget.deleted_at = datetime.now(timezone.utc)  
    
    await db.commit()
    
    return None

@router.get("/{widget_id}/data")
async def get_widget_data(
    widget_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get data for widget visualization"""
    # Get widget
    result = await db.execute(
        select(Widget)
        .join(Dashboard)
        .where(Widget.id == widget_id)
        .where(Dashboard.org_id == organization.id)
    )
    widget = result.scalar_one_or_none()
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # Get data source
    if not widget.data_source_id:
        return {"data": [], "columns": []}
    
    ds_result = await db.execute(
        select(DataSource).where(DataSource.id == widget.data_source_id)
    )
    data_source = ds_result.scalar_one_or_none()
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    # Get latest dataset
    dataset_result = await db.execute(
        select(Dataset)
        .where(Dataset.data_source_id == data_source.id)
        .order_by(Dataset.version.desc())
        .limit(1)
    )
    dataset = dataset_result.scalar_one_or_none()
    
    if not dataset:
        return {"data": [], "columns": []}
    
    # Load data
    df = pd.read_parquet(dataset.storage_path)
    
    # Execute query based on widget config
    executor = QueryExecutor()
    result_data = await executor.execute_widget_query(df, widget.config, widget.widget_type)
    
    # Convert to JSON-safe format using pandas built-in serialization
    # to_json() handles NaN, Inf, and -Inf automatically
    if 'data' in result_data and result_data['data']:
        import json
        # Convert the data list back to DataFrame, then use to_json for safe serialization
        temp_df = pd.DataFrame(result_data['data'])
        result_data['data'] = json.loads(temp_df.to_json(orient='records', date_format='iso'))
    
    return result_data

@router.post("/{widget_id}/refresh")
async def refresh_widget_data(
    widget_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Refresh widget data (trigger data source sync)"""
    result = await db.execute(
        select(Widget)
        .join(Dashboard)
        .where(Widget.id == widget_id)
        .where(Dashboard.org_id == organization.id)
    )
    widget = result.scalar_one_or_none()
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    if widget.data_source_id:
        from app.workers.data_sync import process_data_source
        background_tasks.add_task(process_data_source, str(widget.data_source_id))
    
    return {"status": "refreshing"}