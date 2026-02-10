from sqlalchemy import Column, String, ForeignKey, Text, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import BaseModel

class Widget(BaseModel):
    __tablename__ = "widgets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False)
    data_source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True)
    
    # Widget identification
    widget_type = Column(String(50), nullable=False)  # line, bar, pie, area, scatter, metric, table, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Layout (grid system: 12 columns)
    position = Column(JSONB, nullable=False, default={})  # {x, y, w, h}
    
    # Configuration (separate data query from visual config)
    query_config = Column(JSONB, default={})  # Data query: {x_axis, y_axis, aggregation, filters, group_by}
    chart_config = Column(JSONB, default={})  # Visual config: {colors, legend, grid, custom_options}
    data_mapping = Column(JSONB, default={})  # Column to chart axis mapping
    
    # AI Generation metadata
    generated_by_ai = Column(Boolean, default=False)
    generation_prompt = Column(Text, nullable=True)
    ai_reasoning = Column(Text, nullable=True)  # Why this chart was chosen
    
    # Data caching
    cache_duration_seconds = Column(Integer, default=300)  # 5 minutes default
    last_data_fetch = Column(DateTime(timezone=True), nullable=True)
    cached_data = Column(JSONB, nullable=True)
    
    # Relationships
    dashboard = relationship("Dashboard", back_populates="widgets")
    data_source = relationship("DataSource", back_populates="widgets")