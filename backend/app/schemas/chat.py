from pydantic import BaseModel, Field, UUID4
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


# Base Schemas
class ChatMessageBase(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    message_type: str = "text"
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class ChatSessionBase(BaseModel):
    data_source_id: Optional[UUID4] = None
    title: Optional[str] = None
    status: str = "active"


class DashboardGenerationBase(BaseModel):
    generation_prompt: Optional[str] = None
    is_refinement: bool = False
    parent_generation_id: Optional[UUID4] = None


# Request Schemas
class ChatSessionCreate(BaseModel):
    """Create a new chat session"""
    data_source_id: Optional[UUID4] = None
    title: Optional[str] = None
    initial_message: Optional[str] = None


class ChatMessageCreate(BaseModel):
    """Send a message in a chat session"""
    content: str
    context: Optional[List[Dict[str, str]]] = None  # Optional conversation context


class DashboardGenerationRequest(BaseModel):
    """Generate or refine a dashboard"""
    data_source_id: UUID4
    query: str
    context: Optional[List[Dict[str, str]]] = Field(default_factory=list)
    refinement: bool = False
    existing_dashboard_id: Optional[UUID4] = None


class DashboardFeedbackRequest(BaseModel):
    """Provide feedback on a generated dashboard"""
    generation_id: UUID4
    feedback_score: int = Field(ge=1, le=5)


class TemplateSaveRequest(BaseModel):
    """Save a dashboard as a template"""
    dashboard_id: UUID4
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_public: bool = False


# Response Schemas
class ChatMessageResponse(BaseModel):
    """Chat message response"""
    id: UUID4
    session_id: UUID4
    role: str
    content: str
    message_type: str
    meta_data: Dict[str, Any]
    token_count: int
    processing_time_ms: Optional[int]
    created_at: datetime
    widget_previews: Optional[List[Dict[str, Any]]] = None  # Widgets with preview data
    dashboard_id: Optional[UUID4] = None  # Dashboard ID if created
    
    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    """Chat session response"""
    id: UUID4
    user_id: UUID4
    organization_id: UUID4
    data_source_id: Optional[UUID4]
    title: Optional[str]
    status: str
    meta_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime
    message_count: int = 0
    
    class Config:
        from_attributes = True


class ChatSessionWithMessages(ChatSessionResponse):
    """Chat session with messages"""
    messages: List[ChatMessageResponse]


class DashboardGenerationResponse(BaseModel):
    """Dashboard generation response"""
    dashboard_id: UUID4
    generation_id: UUID4
    explanation: str
    charts: List[Dict[str, Any]]
    insights: List[Dict[str, Any]]
    suggestions: List[str]
    processing_time_ms: int


class DashboardTemplateResponse(BaseModel):
    """Dashboard template response"""
    id: UUID4
    name: str
    description: Optional[str]
    category: Optional[str]
    intent_patterns: Dict[str, Any]
    chart_configs: Dict[str, Any]
    usage_count: int
    success_rate: Optional[float]
    is_public: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuickActionResponse(BaseModel):
    """Quick action suggestions"""
    label: str
    prompt: str
    category: str
    icon: Optional[str] = None


class ChatContextResponse(BaseModel):
    """Context information for chat"""
    session: ChatSessionResponse
    data_source: Optional[Dict[str, Any]] = None
    quick_actions: List[QuickActionResponse]
    recent_dashboards: List[Dict[str, Any]]


class ChatStreamChunk(BaseModel):
    """Streaming response chunk"""
    type: Literal["text", "insight", "chart", "dashboard", "error", "done"]
    content: str
    meta_data: Optional[Dict[str, Any]] = None


# List Schemas
class ChatSessionList(BaseModel):
    """List of chat sessions"""
    sessions: List[ChatSessionResponse]
    total: int
    page: int
    page_size: int


class DashboardTemplateList(BaseModel):
    """List of dashboard templates"""
    templates: List[DashboardTemplateResponse]
    total: int
    page: int
    page_size: int
