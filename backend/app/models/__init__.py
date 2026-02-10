"""
Models package - Import all models here to ensure SQLAlchemy can resolve relationships
"""
from app.db.base import Base, BaseModel

# Import all models in dependency order
from app.models.organization import Organization
from app.models.user import User
from app.models.data_source import DataSource, Dataset, DataSourceStatus, DataSourceType, SyncFrequency
from app.models.dashboard import Dashboard
from app.models.widget import Widget
from app.models.insight import Insight
from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.chat import ChatSession, ChatMessage, DashboardGeneration, DashboardTemplate

# Export all models
__all__ = [
    'Base',
    'BaseModel',
    'Organization',
    'User',
    'DataSource',
    'Dataset',
    'DataSourceStatus',
    'DataSourceType',
    'SyncFrequency',
    'Dashboard',
    'Widget',
    'Insight',
    'Alert',
    'AuditLog',
    'ChatSession',
    'ChatMessage',
    'DashboardGeneration',
    'DashboardTemplate',
]
