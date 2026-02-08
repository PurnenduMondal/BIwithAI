from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, List, Any
from uuid import UUID
import pandas as pd
import numpy as np

from app.db.session import get_db
from app.api.deps import get_current_user, get_user_organization
from app.models.user import User
from app.models.organization import Organization
from app.models.data_source import DataSource, Dataset
from app.services.ai.insight_generator import InsightGenerator
from app.services.analytics.forecasting import ForecastingService
from app.services.analytics.correlation_analyzer import CorrelationAnalyzer

router = APIRouter()

@router.post("/query")
async def nlp_query(
    data_source_id: UUID,
    query: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Process natural language query"""
    # Get data source
    result = await db.execute(
        select(DataSource)
        .where(DataSource.id == data_source_id)
        .where(DataSource.org_id == organization.id)
    )
    data_source = result.scalar_one_or_none()
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    # Get latest dataset
    dataset_result = await db.execute(
        select(Dataset)
        .where(Dataset.data_source_id == data_source_id)
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
    
    # Process query with AI
    generator = InsightGenerator()
    response = await generator.generate_nlp_query_response(query, df, schema)
    
    return response

@router.get("/forecast")
async def forecast_metric(
    data_source_id: UUID,
    metric: str,
    periods: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Generate forecast for a metric"""
    # Get data source
    result = await db.execute(
        select(DataSource)
        .where(DataSource.id == data_source_id)
        .where(DataSource.org_id == organization.id)
    )
    data_source = result.scalar_one_or_none()
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    # Get latest dataset
    dataset_result = await db.execute(
        select(Dataset)
        .where(Dataset.data_source_id == data_source_id)
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
    
    # Check if metric exists
    if metric not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Metric '{metric}' not found"
        )
    
    # Check if time column exists
    time_col = schema.get('time_column')
    if not time_col:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No time column found for forecasting"
        )
    
    # Generate forecast
    forecaster = ForecastingService()
    forecast = await forecaster.forecast(df, time_col, metric, periods)
    
    return forecast

@router.post("/correlation", response_model=Dict[str, Any])
async def analyze_correlations(
    data_source_id: UUID,
    metrics: List[str] = Query(..., min_items=2),
    method: str = Query("pearson", pattern="^(pearson|spearman|kendall)$"),
    min_correlation: float = Query(0.0, ge=0.0, le=1.0),
    max_p_value: float = Query(0.05, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Analyze correlations between metrics"""
    # Get data source
    ds_result = await db.execute(
        select(DataSource).where(
            DataSource.id == data_source_id,
            DataSource.org_id == organization.id
        )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dataset available"
        )
    
    # Load data
    df = pd.read_parquet(dataset.storage_path)
    
    # Validate metrics exist
    missing_metrics = [m for m in metrics if m not in df.columns]
    if missing_metrics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Metrics not found: {missing_metrics}"
        )
    
    # Select only requested metrics
    df_metrics = df[metrics]
    
    # Calculate correlations
    analyzer = CorrelationAnalyzer()
    correlations = await analyzer.analyze(
        df_metrics,
        method=method,
        min_correlation=min_correlation,
        max_p_value=max_p_value
    )
    
    return correlations

@router.get("/anomalies")
async def detect_anomalies(
    data_source_id: UUID,
    metric: str,
    threshold: float = Query(default=2.0, ge=1.0, le=5.0),
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Detect anomalies in a metric"""
    # Get data source
    result = await db.execute(
        select(DataSource)
        .where(DataSource.id == data_source_id)
        .where(DataSource.org_id == organization.id)
    )
    data_source = result.scalar_one_or_none()
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    # Get latest dataset
    dataset_result = await db.execute(
        select(Dataset)
        .where(Dataset.data_source_id == data_source_id)
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
    
    if metric not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Metric '{metric}' not found"
        )
    
    # Detect anomalies using Z-score
    values = df[metric].dropna()
    mean = values.mean()
    std = values.std()
    
    z_scores = np.abs((values - mean) / std)
    anomalies = df[z_scores > threshold]
    
    return {
        "metric": metric,
        "threshold": threshold,
        "total_records": len(df),
        "anomaly_count": len(anomalies),
        "anomalies": anomalies.to_dict(orient='records')
    }