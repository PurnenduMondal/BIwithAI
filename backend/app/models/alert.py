from sqlalchemy import Column, ForeignKey, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import BaseModel

class Alert(BaseModel):
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboards.id"), nullable=False)
    widget_id = Column(UUID(as_uuid=True), ForeignKey("widgets.id"), nullable=True)
    
    condition = Column(JSONB, nullable=False)  # Threshold rules
    notification_channels = Column(JSONB, default=[])  # email, slack, webhook
    is_active = Column(Boolean, default=True)
    
    # Relationships
    dashboard = relationship("Dashboard", back_populates="alerts")
    history = relationship("AlertHistory", back_populates="alert", cascade="all, delete-orphan")

class AlertHistory(BaseModel):
    __tablename__ = "alert_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id"), nullable=False)
    
    triggered_at = Column(DateTime(timezone=True), nullable=False)
    value = Column(JSONB, nullable=False)
    notification_sent = Column(Boolean, default=False)
    
    # Relationships
    alert = relationship("Alert", back_populates="history")