from sqlalchemy import Column, String, Enum as SQLEnum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import uuid
import enum

from app.db.base import BaseModel

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

class User(BaseModel):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    _role = Column("role", String(50), default=UserRole.VIEWER.value, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    @hybrid_property
    def role(self) -> UserRole:
        """Get role as UserRole enum"""
        return UserRole(self._role) if self._role else UserRole.VIEWER
    
    @role.setter
    def role(self, value):
        """Set role from UserRole enum or string"""
        if isinstance(value, UserRole):
            self._role = value.value
        elif isinstance(value, str):
            self._role = value
        else:
            self._role = str(value)
    
    # Relationships
    dashboards = relationship("Dashboard", back_populates="creator", cascade="all, delete-orphan")
    data_sources = relationship("DataSource", back_populates="creator", cascade="all, delete-orphan")
    organization_memberships = relationship("OrganizationMember", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"