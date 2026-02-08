from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class AlertCondition(BaseModel):
    """Alert condition configuration"""
    metric: str
    operator: str  # gt, lt, gte, lte, eq, neq
    threshold: float
    aggregation: Optional[str] = "last"  # last, avg, sum, min, max
    time_window: Optional[int] = None  # minutes

class NotificationChannel(BaseModel):
    """Notification channel configuration"""
    type: str  # email, slack, webhook
    config: Dict[str, Any]

class AlertBase(BaseModel):
    dashboard_id: UUID
    widget_id: Optional[UUID] = None
    condition: Dict[str, Any]
    notification_channels: List[Dict[str, Any]] = []
    is_active: bool = True

class AlertCreate(AlertBase):
    @validator('condition')
    def validate_condition(cls, v):
        required_fields = ['metric', 'operator', 'threshold']
        if not all(field in v for field in required_fields):
            raise ValueError(f"Condition must include: {required_fields}")
        
        valid_operators = ['gt', 'lt', 'gte', 'lte', 'eq', 'neq']
        if v['operator'] not in valid_operators:
            raise ValueError(f"Operator must be one of: {valid_operators}")
        
        return v

class AlertUpdate(BaseModel):
    condition: Optional[Dict[str, Any]] = None
    notification_channels: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None

class AlertResponse(AlertBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AlertHistoryResponse(BaseModel):
    id: UUID
    alert_id: UUID
    triggered_at: datetime
    value: Dict[str, Any]
    notification_sent: bool
    
    class Config:
        from_attributes = True

class AlertWithHistory(AlertResponse):
    history: List[AlertHistoryResponse]
    total_triggers: int