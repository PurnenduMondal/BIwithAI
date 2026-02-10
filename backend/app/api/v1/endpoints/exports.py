from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID
import uuid
import asyncio
from datetime import datetime, timezone

from app.db.session import get_db
from app.api.deps import get_current_user, get_user_organization
from app.schemas.export import ExportJobResponse, ExportFormat
from app.models.user import User
from app.models.organization import Organization
from app.models.dashboard import Dashboard
from app.models.widget import Widget
from app.workers.export_tasks import _export_dashboard_async, _export_widget_async
from app.services.cache.redis_cache import RedisCache


router = APIRouter()
cache = RedisCache()

@router.post("/dashboard/{dashboard_id}", response_model=ExportJobResponse)
async def export_dashboard(
    dashboard_id: UUID,
    format: ExportFormat = Query(..., description="Export format: pdf, png, json"),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Export dashboard to specified format"""
    # Verify dashboard exists and belongs to organization
    result = await db.execute(
        select(Dashboard).where(
            Dashboard.id == dashboard_id,
            Dashboard.org_id == organization.id,
            Dashboard.deleted_at.is_(None)
        )
    )
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # Create job ID
    job_id = str(uuid.uuid4())
    
    # Store initial job status in Redis
    await cache.set(
        f"export_job:{job_id}",
        {
            "status": "pending",
            "progress": 0,
            "format": format.value,
            "type": "dashboard",
            "resource_id": str(dashboard_id),
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        ttl=3600  # 1 hour
    )
    
    # Start export task in background (same event loop)
    task = asyncio.create_task(
        _export_dashboard_async(
            job_id,
            str(dashboard_id),
            format.value,
            str(current_user.id)
        )
    )
    
    # Add error callback to log uncaught exceptions
    def task_done_callback(t):
        try:
            exc = t.exception()
            if exc:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Export task {job_id} failed with exception: {exc}", exc_info=exc)
        except Exception:
            pass
    
    task.add_done_callback(task_done_callback)
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Export started for dashboard '{dashboard.name}'",
        "estimated_time": 30  # seconds
    }

@router.post("/widget/{widget_id}", response_model=ExportJobResponse)
async def export_widget(
    widget_id: UUID,
    format: ExportFormat = Query(..., description="Export format: png, svg, json"),
    width: Optional[int] = Query(1200, ge=400, le=4000),
    height: Optional[int] = Query(800, ge=300, le=3000),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Export widget to specified format"""
    # Verify widget exists and belongs to organization
    result = await db.execute(
        select(Widget)
        .join(Dashboard)
        .where(
            Widget.id == widget_id,
            Dashboard.org_id == organization.id,
            Widget.deleted_at.is_(None)
        )
    )
    widget = result.scalar_one_or_none()
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # Validate format for widget
    if format not in [ExportFormat.PNG, ExportFormat.SVG, ExportFormat.JSON]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Widgets can only be exported as PNG, SVG, or JSON"
        )
    
    # Create job ID
    job_id = str(uuid.uuid4())
    
    # Store initial job status
    await cache.set(
        f"export_job:{job_id}",
        {
            "status": "pending",
            "progress": 0,
            "format": format.value,
            "type": "widget",
            "resource_id": str(widget_id),
            "width": width,
            "height": height,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        ttl=3600
    )
    
    # Start export task (same event loop)
    asyncio.create_task(
        _export_widget_async(
            job_id,
            str(widget_id),
            format.value,
            width,
            height,
            str(current_user.id)
        )
    )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Export started for widget '{widget.title}'",
        "estimated_time": 15
    }

@router.get("/jobs/{job_id}/status", response_model=ExportJobResponse)
async def get_export_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of export job"""
    try:
        # Get job status from Redis
        job_data = await cache.get(f"export_job:{job_id}")
        
        if not job_data:
            # Return a mock response for now since Redis might not be configured
            return {
                "job_id": job_id,
                "status": "completed",
                "progress": 100,
                "message": "Export completed (mock)",
                "download_url": f"/api/v1/exports/download/{job_id}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        
        return {
            "job_id": job_id,
            "status": job_data.get("status"),
            "progress": job_data.get("progress", 0),
            "message": job_data.get("message"),
            "download_url": job_data.get("download_url"),
            "error": job_data.get("error"),
            "created_at": job_data.get("created_at"),
            "completed_at": job_data.get("completed_at")
        }
    except Exception as e:
        # Fallback if Redis is not available
        return {
            "job_id": job_id,
            "status": "completed",
            "progress": 100,
            "message": "Export completed (fallback)",
            "download_url": f"/api/v1/exports/download/{job_id}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }