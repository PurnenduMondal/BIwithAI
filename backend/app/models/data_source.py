from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import uuid
import enum

from app.db.base import BaseModel

class DataSourceType(str, enum.Enum):
    CSV = "csv"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    API = "api"
    GOOGLE_SHEETS = "google_sheets"

class DataSourceStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ERROR = "error"
    SYNCING = "syncing"

class SyncFrequency(str, enum.Enum):
    MANUAL = "manual"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"

class DataSource(BaseModel):
    __tablename__ = "data_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    _type = Column("type", String(50), nullable=False)
    connection_config = Column(JSONB, nullable=False)  # Encrypted
    schema_metadata = Column(JSONB, default={})
    
    _status = Column("status", String(50), default=DataSourceStatus.PENDING.value)
    _sync_frequency = Column("sync_frequency", String(50), default=SyncFrequency.MANUAL.value)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    
    @hybrid_property
    def type(self) -> DataSourceType:
        """Get type as DataSourceType enum"""
        return DataSourceType(self._type) if self._type else None
    
    @type.setter
    def type(self, value):
        """Set type from DataSourceType enum or string"""
        if isinstance(value, DataSourceType):
            self._type = value.value
        elif isinstance(value, str):
            self._type = value
        else:
            self._type = str(value)
    
    @hybrid_property
    def status(self) -> DataSourceStatus:
        """Get status as DataSourceStatus enum"""
        return DataSourceStatus(self._status) if self._status else DataSourceStatus.PENDING
    
    @status.setter
    def status(self, value):
        """Set status from DataSourceStatus enum or string"""
        if isinstance(value, DataSourceStatus):
            self._status = value.value
        elif isinstance(value, str):
            self._status = value
        else:
            self._status = str(value)
    
    @hybrid_property
    def sync_frequency(self) -> SyncFrequency:
        """Get sync_frequency as SyncFrequency enum"""
        return SyncFrequency(self._sync_frequency) if self._sync_frequency else SyncFrequency.MANUAL
    
    @sync_frequency.setter
    def sync_frequency(self, value):
        """Set sync_frequency from SyncFrequency enum or string"""
        if isinstance(value, SyncFrequency):
            self._sync_frequency = value.value
        elif isinstance(value, str):
            self._sync_frequency = value
        else:
            self._sync_frequency = str(value)
    
    # Relationships
    organization = relationship("Organization", back_populates="data_sources")
    creator = relationship("User", back_populates="data_sources")
    datasets = relationship("Dataset", back_populates="data_source", cascade="all, delete-orphan")
    widgets = relationship("Widget", back_populates="data_source")

class Dataset(BaseModel):
    __tablename__ = "datasets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False)
    
    version = Column(Integer, nullable=False)
    row_count = Column(Integer, nullable=False)
    column_count = Column(Integer, nullable=False)
    data_profile = Column(JSONB, default={})
    storage_path = Column(String(500), nullable=False)  # S3/MinIO path
    
    # Relationships
    data_source = relationship("DataSource", back_populates="datasets")