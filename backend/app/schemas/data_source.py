from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.data_source import DataSourceType, DataSourceStatus, SyncFrequency

class DataSourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: DataSourceType

class DataSourceCreate(DataSourceBase):
    connection_config: Dict[str, Any]
    sync_frequency: SyncFrequency = SyncFrequency.MANUAL
    
    @validator('connection_config')
    def validate_connection_config(cls, v, values):
        ds_type = values.get('type')
        
        if ds_type == DataSourceType.POSTGRESQL:
            required = ['host', 'port', 'database', 'username', 'password']
            if not all(k in v for k in required):
                raise ValueError(f'PostgreSQL requires: {required}')
        
        elif ds_type == DataSourceType.CSV:
            if 'file_path' not in v:
                raise ValueError('CSV requires file_path')
        
        return v

class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    sync_frequency: Optional[SyncFrequency] = None
    connection_config: Optional[Dict[str, Any]] = None

class DataSourceResponse(DataSourceBase):
    id: UUID
    org_id: UUID
    status: DataSourceStatus
    schema_metadata: Dict[str, Any]
    last_sync: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DataSourceWithStats(DataSourceResponse):
    total_rows: int
    total_columns: int
    last_dataset_version: Optional[int]