from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import datetime, timezone, timedelta
import psutil

from app.db.session import get_db
from app.api.deps import get_current_admin_user
from app.schemas.admin import (
    UsageStatsResponse,
    AuditLogResponse,
    SystemHealthResponse
)
from app.models.user import User
from app.models.organization import Organization
from app.models.dashboard import Dashboard
from app.models.data_source import DataSource
from app.models.audit_log import AuditLog

router = APIRouter()

@router.get("/usage-stats", response_model=UsageStatsResponse)
async def get_usage_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get platform usage statistics (admin only)"""
    
    # Default to last 30 days
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Total users
    total_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    total_users = total_users_result.scalar()
    
    # New users in period
    new_users_result = await db.execute(
        select(func.count(User.id)).where(
            User.created_at >= start_date,
            User.created_at <= end_date
        )
    )
    new_users = new_users_result.scalar()
    
    # Active users (logged in during period)
    active_users_result = await db.execute(
        select(func.count(User.id)).where(
            User.last_login >= start_date,
            User.last_login <= end_date
        )
    )
    active_users = active_users_result.scalar()
    
    # Total organizations
    total_orgs_result = await db.execute(
        select(func.count(Organization.id)).where(Organization.is_active == True)
    )
    total_orgs = total_orgs_result.scalar()
    
    # Total dashboards
    total_dashboards_result = await db.execute(
        select(func.count(Dashboard.id)).where(Dashboard.deleted_at.is_(None))
    )
    total_dashboards = total_dashboards_result.scalar()
    
    # Dashboards created in period
    new_dashboards_result = await db.execute(
        select(func.count(Dashboard.id)).where(
            Dashboard.created_at >= start_date,
            Dashboard.created_at <= end_date,
            Dashboard.deleted_at.is_(None)
        )
    )
    new_dashboards = new_dashboards_result.scalar()
    
    # Total data sources
    total_datasources_result = await db.execute(
        select(func.count(DataSource.id)).where(DataSource.deleted_at.is_(None))
    )
    total_datasources = total_datasources_result.scalar()
    
    # Data sources by type
    datasources_by_type_result = await db.execute(
        select(DataSource.type, func.count(DataSource.id))
        .where(DataSource.deleted_at.is_(None))
        .group_by(DataSource.type)
    )
    datasources_by_type = dict(datasources_by_type_result.all())
    
    # Most active organizations (by dashboard count)
    top_orgs_result = await db.execute(
        select(
            Organization.id,
            Organization.name,
            func.count(Dashboard.id).label('dashboard_count')
        )
        .join(Dashboard)
        .where(Dashboard.deleted_at.is_(None))
        .group_by(Organization.id, Organization.name)
        .order_by(func.count(Dashboard.id).desc())
        .limit(10)
    )
    top_orgs = [
        {"org_id": str(row[0]), "name": row[1], "dashboard_count": row[2]}
        for row in top_orgs_result.all()
    ]
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "users": {
            "total": total_users,
            "new": new_users,
            "active": active_users
        },
        "organizations": {
            "total": total_orgs
        },
        "dashboards": {
            "total": total_dashboards,
            "created_in_period": new_dashboards
        },
        "data_sources": {
            "total": total_datasources,
            "by_type": datasources_by_type
        },
        "top_organizations": top_orgs
    }

@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs (admin only)"""
    
    query = select(AuditLog)
    
    filters = []
    
    if user_id:
        filters.append(AuditLog.user_id == user_id)
    
    if action:
        filters.append(AuditLog.action == action)
    
    if resource_type:
        filters.append(AuditLog.resource_type == resource_type)
    
    if start_date:
        filters.append(AuditLog.created_at >= start_date)
    
    if end_date:
        filters.append(AuditLog.created_at <= end_date)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(AuditLog.created_at.desc())
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return logs

@router.get("/system-health", response_model=SystemHealthResponse)
async def get_system_health(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system health metrics (admin only)"""
    
    # Database connection
    try:
        await db.execute(select(1))
        db_status = "healthy"
        db_latency = 0  # You can measure actual latency
    except Exception:
        db_status = "unhealthy"
        db_latency = None
    
    # Redis connection
    from app.services.cache.redis_cache import RedisCache
    cache = RedisCache()
    
    try:
        await cache.set("health_check", "ok", ttl=60)
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"
    
    # System resources
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Celery workers (check if workers are running)
    from app.workers.celery_app import celery_app
    
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        celery_status = "healthy" if active_workers else "no_workers"
        worker_count = len(active_workers) if active_workers else 0
    except Exception:
        celery_status = "unhealthy"
        worker_count = 0
    
    # Calculate overall health
    all_healthy = all([
        db_status == "healthy",
        redis_status == "healthy",
        celery_status == "healthy",
        cpu_percent < 90,
        memory.percent < 90,
        disk.percent < 90
    ])
    
    overall_status = "healthy" if all_healthy else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "database": {
                "status": db_status,
                "latency_ms": db_latency
            },
            "redis": {
                "status": redis_status
            },
            "celery": {
                "status": celery_status,
                "worker_count": worker_count
            }
        },
        "resources": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_total_gb": memory.total / (1024**3),
            "disk_percent": disk.percent,
            "disk_used_gb": disk.used / (1024**3),
            "disk_total_gb": disk.total / (1024**3)
        }
    }