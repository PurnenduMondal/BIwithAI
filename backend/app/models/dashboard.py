from sqlalchemy import Column, String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import BaseModel

class Dashboard(BaseModel):
    __tablename__ = "dashboards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    layout_config = Column(JSONB, default={})
    filters = Column(JSONB, default=[])
    theme = Column(JSONB, default={})
    
    is_template = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    public_share_token = Column(String(100), unique=True, nullable=True)
    
    # AI Generation fields
    generated_by_ai = Column(Boolean, default=False)
    generation_context = Column(JSONB, default={})
    template_id = Column(UUID(as_uuid=True), ForeignKey("dashboard_templates.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="dashboards")
    creator = relationship("User", back_populates="dashboards")
    widgets = relationship("Widget", back_populates="dashboard", cascade="all, delete-orphan")
    insights = relationship("Insight", back_populates="dashboard", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="dashboard", cascade="all, delete-orphan")
    generations = relationship("DashboardGeneration", back_populates="dashboard", cascade="all, delete-orphan")