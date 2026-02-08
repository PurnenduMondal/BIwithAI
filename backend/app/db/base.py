from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, Boolean
from datetime import datetime, timezone
from typing import Any

Base = declarative_base()

def utc_now():
    """Return timezone-aware UTC datetime"""
    return datetime.now(timezone.utc)

class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    is_active = Column(Boolean, default=True, nullable=False)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }