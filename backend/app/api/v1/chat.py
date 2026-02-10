from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.ai.chat_service import DashboardChatService
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionWithMessages,
    ChatSessionList,
    ChatMessageCreate,
    ChatMessageResponse,
    DashboardGenerationRequest,
    DashboardGenerationResponse,
    DashboardFeedbackRequest,
    ChatContextResponse,
    QuickActionResponse,
)

router = APIRouter(prefix="/chat", tags=["AI Chat"])


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    request: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session for dashboard generation"""
    chat_service = DashboardChatService(db)
    
    session = await chat_service.create_session(
        user_id=current_user.id,
        org_id=current_user.organization_memberships[0].org_id,  # Should use proper org context
        data_source_id=request.data_source_id,
        title=request.title
    )
    
    # Add message count
    session.message_count = 0
    
    return session


@router.get("/sessions", response_model=ChatSessionList)
async def list_chat_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's chat sessions"""
    chat_service = DashboardChatService(db)
    
    result = await chat_service.get_user_sessions(
        user_id=current_user.id,
        org_id=current_user.organization_memberships[0].org_id,
        page=page,
        page_size=page_size
    )
    
    return result


@router.get("/sessions/{session_id}", response_model=ChatSessionWithMessages)
async def get_chat_session(
    session_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a chat session with its messages"""
    chat_service = DashboardChatService(db)
    
    try:
        result = await chat_service.get_session_with_messages(
            session_id=session_id,
            user_id=current_user.id,
            limit=limit
        )
        
        return {
            **result["session"].__dict__,
            "messages": result["messages"],
            "message_count": result["message_count"]
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: UUID,
    request: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message in a chat session"""
    chat_service = DashboardChatService(db)
    
    try:
        result = await chat_service.send_message(
            session_id=session_id,
            user_message=request.content,
            user_id=current_user.id
        )
        
        return result["message"]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/generate", response_model=DashboardGenerationResponse)
async def generate_dashboard(
    request: DashboardGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a dashboard from a natural language query"""
    chat_service = DashboardChatService(db)
    
    # Create a session if one doesn't exist
    # In a real implementation, this should be passed or created separately
    from app.models.chat import ChatSession
    
    # Try to find or create session
    session = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatSession.data_source_id == request.data_source_id,
        ChatSession.status == "active"
    ).order_by(ChatSession.last_message_at.desc()).first()
    
    if not session:
        session = await chat_service.create_session(
            user_id=current_user.id,
            org_id=current_user.organization_memberships[0].org_id,
            data_source_id=request.data_source_id,
            title=f"Dashboard: {request.query[:30]}"
        )
    
    try:
        result = await chat_service.generate_dashboard(
            session_id=session.id,
            data_source_id=request.data_source_id,
            query=request.query,
            user_id=current_user.id,
            refinement=request.refinement,
            existing_dashboard_id=request.existing_dashboard_id
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/generations/{generation_id}/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def submit_feedback(
    generation_id: UUID,
    request: DashboardFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback for a dashboard generation"""
    from app.models.chat import DashboardGeneration
    
    generation = db.query(DashboardGeneration).filter(
        DashboardGeneration.id == generation_id
    ).first()
    
    if not generation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation not found")
    
    # Verify user owns the session
    if generation.session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    generation.feedback_score = request.feedback_score
    db.commit()
    
    return None


@router.get("/quick-actions", response_model=List[QuickActionResponse])
async def get_quick_actions(
    data_source_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quick action suggestions"""
    chat_service = DashboardChatService(db)
    return chat_service.get_quick_actions(data_source_id)


@router.get("/context/{session_id}", response_model=ChatContextResponse)
async def get_chat_context(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get context information for a chat session"""
    from app.models.chat import ChatSession
    from app.models.dashboard import Dashboard
    from app.models.data_source import DataSource
    
    chat_service = DashboardChatService(db)
    
    # Get session
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    # Get data source info
    data_source = None
    if session.data_source_id:
        ds = db.query(DataSource).filter(DataSource.id == session.data_source_id).first()
        if ds:
            data_source = {
                "id": str(ds.id),
                "name": ds.name,
                "type": ds.type.value
            }
    
    # Get recent dashboards from this session
    from app.models.chat import DashboardGeneration
    recent_gens = db.query(DashboardGeneration).filter(
        DashboardGeneration.session_id == session_id
    ).order_by(DashboardGeneration.created_at.desc()).limit(5).all()
    
    recent_dashboards = []
    for gen in recent_gens:
        dashboard = db.query(Dashboard).filter(Dashboard.id == gen.dashboard_id).first()
        if dashboard:
            recent_dashboards.append({
                "id": str(dashboard.id),
                "name": dashboard.name,
                "created_at": dashboard.created_at.isoformat()
            })
    
    # Add message count
    session.message_count = 0
    
    return {
        "session": session,
        "data_source": data_source,
        "quick_actions": chat_service.get_quick_actions(session.data_source_id),
        "recent_dashboards": recent_dashboards
    }


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session"""
    from app.models.chat import ChatSession
    
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    db.delete(session)
    db.commit()
    
    return None


@router.patch("/sessions/{session_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def archive_chat_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Archive a chat session"""
    from app.models.chat import ChatSession
    
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    session.status = "archived"
    db.commit()
    
    return None
