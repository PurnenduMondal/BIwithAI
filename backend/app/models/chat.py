from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text, TIMESTAMP, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class ChatSession(Base):
    """Chat sessions for AI-powered dashboard generation"""
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    data_source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="active")
    meta_data = Column(JSONB, nullable=False, default={})
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_message_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    organization = relationship("Organization", back_populates="chat_sessions")
    data_source = relationship("DataSource", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")
    dashboard_generations = relationship("DashboardGeneration", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'completed', 'archived')", name="valid_status"),
    )


class ChatMessage(Base):
    """Individual messages within a chat session"""
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(50), nullable=False, default="text")
    meta_data = Column(JSONB, nullable=False, default={})
    token_count = Column(Integer, nullable=False, default=0)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    dashboard_generations = relationship("DashboardGeneration", back_populates="message")
    
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="valid_role"),
    )


class DashboardGeneration(Base):
    """Link between chat sessions and generated dashboards"""
    __tablename__ = "dashboard_generations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id", ondelete="SET NULL"), nullable=True)
    generation_prompt = Column(Text, nullable=True)
    is_refinement = Column(Boolean, nullable=False, default=False)
    parent_generation_id = Column(UUID(as_uuid=True), ForeignKey("dashboard_generations.id", ondelete="SET NULL"), nullable=True)
    feedback_score = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="dashboard_generations")
    dashboard = relationship("Dashboard", back_populates="generations")
    message = relationship("ChatMessage", back_populates="dashboard_generations")
    parent_generation = relationship("DashboardGeneration", remote_side=[id], backref="refinements")
    
    __table_args__ = (
        CheckConstraint("feedback_score IS NULL OR (feedback_score >= 1 AND feedback_score <= 5)", name="valid_feedback"),
    )


class DashboardTemplate(Base):
    """Reusable dashboard templates learned from usage patterns"""
    __tablename__ = "dashboard_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    intent_patterns = Column(JSONB, nullable=False)
    chart_configs = Column(JSONB, nullable=False)
    schema_requirements = Column(JSONB, nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)
    success_rate = Column(Numeric(5, 2), nullable=True)
    created_from_session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True)
    is_public = Column(Boolean, nullable=False, default=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="dashboard_templates")
    created_from_session = relationship("ChatSession", foreign_keys=[created_from_session_id])
