from sqlalchemy import Column, String, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import BaseModel

class Insight(BaseModel):
    __tablename__ = "insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboards.id"), nullable=False)
    widget_id = Column(UUID(as_uuid=True), ForeignKey("widgets.id"), nullable=True)
    
    insight_type = Column(String(50), nullable=False)  # trend, anomaly, recommendation, summary
    content = Column(Text, nullable=False)
    confidence_score = Column(Numeric(3, 2), nullable=False)
    insight_metadata = Column(JSONB, default={})
    
    # Relationships
    dashboard = relationship("Dashboard", back_populates="insights")