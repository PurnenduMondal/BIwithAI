from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import BaseModel

class Widget(BaseModel):
    __tablename__ = "widgets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboards.id"), nullable=False)
    data_source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=True)
    
    widget_type = Column(String(50), nullable=False)  # chart, metric, table, text, ai_insight
    title = Column(String(255), nullable=False)
    position = Column(JSONB, nullable=False)  # {x, y, w, h}
    config = Column(JSONB, default={})  # Chart config, queries, etc.
    
    # Relationships
    dashboard = relationship("Dashboard", back_populates="widgets")
    data_source = relationship("DataSource", back_populates="widgets")