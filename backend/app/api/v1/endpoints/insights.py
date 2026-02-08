from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
import pandas as pd
from datetime import datetime, timezone

from app.db.session import get_db
from app.api.deps import get_current_user, get_user_organization
from app.schemas.insight import InsightResponse, InsightGenerateRequest
from app.models.user import User
from app.models.organization import Organization
from app.models.dashboard import Dashboard
from app.models.insight import Insight
from app.models.data_source import DataSource, Dataset
from app.services.ai.insight_generator import InsightGenerator

router = APIRouter()

@router.get("/dashboards/{dashboard_id}/insights", response_model=List[InsightResponse])
async def list_dashboard_insights(
    dashboard_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """List insights for a dashboard"""
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
    
    result = await db.execute(
        select(Insight)
        .where(Insight.dashboard_id == dashboard_id)
        .where(Insight.deleted_at.is_(None))
        .order_by(Insight.confidence_score.desc(), Insight.created_at.desc())
    )
    insights = result.scalars().all()
    
    return insights

@router.post("/dashboards/{dashboard_id}/insights/generate")
async def generate_insights(
    dashboard_id: UUID,
    request: InsightGenerateRequest = None,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Generate AI insights for dashboard"""
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
    
    # Get dashboard's primary data source (from first widget)
    from app.models.widget import Widget
    widget_result = await db.execute(
        select(Widget)
        .where(Widget.dashboard_id == dashboard_id)
        .where(Widget.data_source_id.isnot(None))
        .limit(1)
    )
    widget = widget_result.scalar_one_or_none()
    
    if not widget or not widget.data_source_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data source found for dashboard"
        )
    
    # Get latest dataset
    dataset_result = await db.execute(
        select(Dataset)
        .where(Dataset.data_source_id == widget.data_source_id)
        .order_by(Dataset.version.desc())
        .limit(1)
    )
    dataset = dataset_result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data available"
        )
    
    # Load data
    df = pd.read_parquet(dataset.storage_path)
    schema = dataset.data_profile
    
    # Generate insights
    generator = InsightGenerator()
    context = request.context if request else ""
    insights = await generator.generate_insights(df, schema, context)
    
    # Save insights to database
    saved_insights = []
    for insight_data in insights:
        insight = Insight(
            dashboard_id=dashboard_id,
            insight_type=insight_data.get('type'),
            content=insight_data.get('description', ''),
            confidence_score=insight_data.get('confidence', 0.5),
            insight_metadata=insight_data
        )
        db.add(insight)
        saved_insights.append(insight)
    
    await db.commit()
    
    return {
        "status": "success",
        "insights_generated": len(saved_insights),
        "insights": saved_insights
    }

@router.get("/insights/{insight_id}", response_model=InsightResponse)
async def get_insight(
    insight_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get specific insight"""
    result = await db.execute(
        select(Insight)
        .join(Dashboard)
        .where(Insight.id == insight_id)
        .where(Dashboard.org_id == organization.id)
    )
    insight = result.scalar_one_or_none()
    
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight not found"
        )
    
    return insight

@router.delete("/insights/{insight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_insight(
    insight_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Delete insight"""
    result = await db.execute(
        select(Insight)
        .join(Dashboard)
        .where(Insight.id == insight_id)
        .where(Dashboard.org_id == organization.id)
    )
    insight = result.scalar_one_or_none()
    
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight not found"
        )
    
    from datetime import datetime
    insight.deleted_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return None