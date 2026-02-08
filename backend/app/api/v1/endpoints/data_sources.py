from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
import aiofiles
import os
import pandas as pd
import numpy as np

from app.db.session import get_db
from app.api.deps import get_current_user, get_user_organization
from app.schemas.data_source import (
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceResponse,
    DataSourceWithStats
)
from app.models.user import User
from app.models.organization import Organization
from app.models.data_source import DataSource, DataSourceStatus, DataSourceType
from app.services.data_ingestion.csv_connector import CSVConnector
from app.services.data_ingestion.database_connector import DatabaseConnector
from app.workers.data_sync import process_data_source
from app.config import settings
from app.models.data_source import Dataset

router = APIRouter()

@router.get("/", response_model=List[DataSourceResponse])
async def list_data_sources(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """List all data sources for the organization"""
    result = await db.execute(
        select(DataSource)
        .where(DataSource.org_id == organization.id)
        .where(DataSource.deleted_at.is_(None))
        .offset(skip)
        .limit(limit)
        .order_by(DataSource.created_at.desc())
    )
    data_sources = result.scalars().all()
    
    return data_sources

@router.post("/", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_data_source(
    data_source_data: DataSourceCreate,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Create a new data source"""
    # Encrypt sensitive connection config
    from app.utils.encryption import encrypt_dict
    encrypted_config = encrypt_dict(data_source_data.connection_config)
    
    # Create data source - Use underlying columns with .value
    data_source = DataSource(
        org_id=organization.id,
        created_by=current_user.id,
        name=data_source_data.name,
        _type=data_source_data.type.value,
        connection_config=encrypted_config,
        _sync_frequency=data_source_data.sync_frequency.value,
        _status=DataSourceStatus.PENDING.value
    )
    
    db.add(data_source)
    await db.commit()
    await db.refresh(data_source)
    
    # Queue Celery task
    process_data_source.delay(str(data_source.id))
    
    return data_source

@router.post("/upload-csv", response_model=DataSourceResponse)
async def upload_csv(
    file: UploadFile = File(...),
    name: str = None,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Upload a CSV file and create a data source"""
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    # Validate file size
    file_size = 0
    chunk_size = 8192  # 8KB chunks
    while chunk := await file.read(chunk_size):
        file_size += len(chunk)
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large"
            )
    
    # Reset file pointer
    await file.seek(0)
    
    # Save file
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(organization.id))
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Create data source
    data_source = DataSource(
        org_id=organization.id,
        created_by=current_user.id,
        name=name or file.filename,
        _type=DataSourceType.CSV.value, 
        connection_config={"file_path": file_path},
        _status=DataSourceStatus.PENDING.value 
    )
    
    db.add(data_source)
    await db.commit()
    await db.refresh(data_source)
    
    # Queue Celery task
    process_data_source.delay(str(data_source.id))
    
    return data_source

@router.get("/{data_source_id}", response_model=DataSourceWithStats)
async def get_data_source(
    data_source_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific data source"""
    result = await db.execute(
        select(DataSource)
        .where(DataSource.id == data_source_id)
        .where(DataSource.org_id == organization.id)
        .where(DataSource.deleted_at.is_(None))
    )
    data_source = result.scalar_one_or_none()
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    # Get stats from latest dataset
    from app.models.data_source import Dataset
    dataset_result = await db.execute(
        select(Dataset)
        .where(Dataset.data_source_id == data_source_id)
        .order_by(Dataset.version.desc())
        .limit(1)
    )
    latest_dataset = dataset_result.scalar_one_or_none()
    
    response_data = data_source.to_dict()
    if latest_dataset:
        response_data.update({
            "total_rows": latest_dataset.row_count,
            "total_columns": latest_dataset.column_count,
            "last_dataset_version": latest_dataset.version
        })
    else:
        response_data.update({
            "total_rows": 0,
            "total_columns": 0,
            "last_dataset_version": None
        })
    
    return response_data

@router.put("/{data_source_id}", response_model=DataSourceResponse)
async def update_data_source(
    data_source_id: UUID,
    update_data: DataSourceUpdate,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Update a data source"""
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
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    
    if 'connection_config' in update_dict:
        from app.utils.encryption import encrypt_dict
        update_dict['connection_config'] = encrypt_dict(update_dict['connection_config'])
    
    # Convert enum fields to underlying column names
    if 'sync_frequency' in update_dict:
        update_dict['_sync_frequency'] = update_dict.pop('sync_frequency').value
    
    for field, value in update_dict.items():
        setattr(data_source, field, value)
    
    await db.commit()
    await db.refresh(data_source)
    
    return data_source

@router.delete("/{data_source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_source(
    data_source_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Delete a data source (soft delete)"""
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
    
    # Soft delete
    from datetime import datetime
    data_source.deleted_at = datetime.utcnow()
    data_source.is_active = False
    
    await db.commit()
    
    return None

@router.post("/{data_source_id}/test-connection")
async def test_connection(
    data_source_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Test data source connection"""
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
    
    try:
        # Decrypt config
        from app.utils.encryption import decrypt_dict
        config = decrypt_dict(data_source.connection_config)
        
        # Test connection based on type
        if data_source.type == "postgresql":
            connector = DatabaseConnector("postgresql", config)
            success = await connector.test_connection()
        elif data_source.type == "mysql":
            connector = DatabaseConnector("mysql", config)
            success = await connector.test_connection()
        elif data_source.type == "csv":
            connector = CSVConnector(config)
            success = connector.test_connection()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported data source type: {data_source.type}"
            )
        
        if success:
            return {"status": "success", "message": "Connection successful"}
        else:
            return {"status": "failed", "message": "Connection failed"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection test failed: {str(e)}"
        )

@router.post("/{data_source_id}/sync")
async def sync_data_source(
    data_source_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger data source sync"""
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
    
    # Update status - Use underlying column
    data_source._status = DataSourceStatus.SYNCING.value
    await db.commit()
    
    # Queue Celery task
    task = process_data_source.delay(str(data_source_id))
    
    return {
        "status": "syncing",
        "message": "Data source sync started",
        "task_id": task.id
    }

@router.get("/{data_source_id}/preview")
async def preview_data(
    data_source_id: UUID,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Preview data from data source"""
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data available yet"
        )
    
    try:
        df = pd.read_parquet(dataset.storage_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data file not found. Please sync the data source again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading data: {str(e)}"
        )
    
    # Get preview subset
    df_preview = df.head(limit)
    
    # Convert to JSON-safe format using pandas built-in serialization
    # to_json() handles NaN, Inf, and -Inf automatically
    import json
    preview_data = json.loads(df_preview.to_json(orient='records', date_format='iso'))
    
    return {
        "columns": list(df.columns),
        "data": preview_data,
        "total_rows": len(df),
        "preview_rows": len(preview_data)
    }

@router.get("/{data_source_id}/schema")
async def get_schema(
    data_source_id: UUID,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get data source schema metadata"""
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
    
    if not data_source.schema_metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schema not available yet. Please sync the data source first."
        )
    
    return data_source.schema_metadata