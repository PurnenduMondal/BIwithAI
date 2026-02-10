import logging
import json
import time
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import pandas as pd

from anthropic import Anthropic

from app.config import settings
from app.models.chat import ChatSession, ChatMessage, DashboardGeneration, DashboardTemplate
from app.models.dashboard import Dashboard
from app.models.widget import Widget
from app.models.data_source import DataSource
from app.services.ai.insight_generator import InsightGenerator
from app.schemas.chat import QuickActionResponse

logger = logging.getLogger(__name__)


class DashboardChatService:
    """Service for AI-powered dashboard generation through chat"""
    
    def __init__(self, db: Session):
        self.db = db
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        self.insight_generator = InsightGenerator()
    
    async def create_session(
        self,
        user_id: UUID,
        org_id: UUID,
        data_source_id: Optional[UUID] = None,
        title: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(
            user_id=user_id,
            organization_id=org_id,
            data_source_id=data_source_id,
            title=title or "New Dashboard Chat"
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"Created chat session {session.id} for user {user_id}")
        return session
    
    async def send_message(
        self,
        session_id: UUID,
        user_message: str,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Process a user message and generate AI response"""
        start_time = time.time()
        
        # Get session
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise ValueError("Session not found")
        
        # Verify user owns session
        if session.user_id != user_id:
            raise PermissionError("Not authorized to access this session")
        
        # Add user message
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=user_message,
            message_type="text"
        )
        self.db.add(user_msg)
        self.db.flush()
        
        # Get conversation context
        context = self._get_conversation_context(session_id)
        
        # Generate AI response based on message intent
        intent = await self._analyze_intent(user_message, context)
        
        if intent["type"] == "dashboard_generation":
            response = await self._handle_dashboard_generation(
                session=session,
                user_message=user_message,
                intent=intent,
                context=context
            )
        elif intent["type"] == "refinement":
            response = await self._handle_dashboard_refinement(
                session=session,
                user_message=user_message,
                intent=intent,
                context=context
            )
        elif intent["type"] == "question":
            response = await self._handle_question(
                session=session,
                user_message=user_message,
                intent=intent,
                context=context
            )
        else:
            response = await self._handle_general_response(
                session=session,
                user_message=user_message,
                context=context
            )
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        # Add assistant message
        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=response["content"],
            message_type=response.get("message_type", "text"),
            meta_data=response.get("meta_data", {}),
            token_count=response.get("token_count", 0),
            processing_time_ms=processing_time
        )
        self.db.add(assistant_msg)
        
        # Update session
        session.last_message_at = datetime.now(timezone.utc)
        if not session.title or session.title == "New Dashboard Chat":
            session.title = self._generate_session_title(user_message)
        
        self.db.commit()
        self.db.refresh(assistant_msg)
        
        logger.info(f"Generated response for session {session_id} in {processing_time}ms")
        
        return {
            "message": assistant_msg,
            "intent": intent,
            "processing_time_ms": processing_time
        }
    
    async def generate_dashboard(
        self,
        session_id: UUID,
        data_source_id: UUID,
        query: str,
        user_id: UUID,
        refinement: bool = False,
        existing_dashboard_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Generate a dashboard based on natural language query"""
        start_time = time.time()
        
        # Get session
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session or session.user_id != user_id:
            raise ValueError("Invalid session")
        
        # Get data source
        data_source = self.db.query(DataSource).filter(DataSource.id == data_source_id).first()
        if not data_source:
            raise ValueError("Data source not found")
        
        # Load data (this should be optimized with caching)
        df, schema = await self._load_data_source(data_source)
        
        # Generate insights
        insights = await self.insight_generator.generate_insights(df, schema, query)
        
        # Generate charts based on query and insights
        charts = await self._generate_charts_for_query(query, df, schema, insights)
        
        # Create or update dashboard
        if refinement and existing_dashboard_id:
            dashboard = await self._refine_dashboard(existing_dashboard_id, charts)
        else:
            dashboard = await self._create_dashboard(
                session=session,
                name=f"AI: {query[:50]}",
                charts=charts,
                insights=insights,
                query=query
            )
        
        # Track generation
        generation = DashboardGeneration(
            session_id=session_id,
            dashboard_id=dashboard.id,
            generation_prompt=query,
            is_refinement=refinement,
            parent_generation_id=existing_dashboard_id if refinement else None
        )
        self.db.add(generation)
        self.db.commit()
        self.db.refresh(generation)
        
        # Generate follow-up suggestions
        suggestions = await self._generate_suggestions(query, insights, schema)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"Generated dashboard {dashboard.id} in {processing_time}ms")
        
        return {
            "dashboard_id": dashboard.id,
            "generation_id": generation.id,
            "explanation": self._generate_explanation(charts, insights),
            "charts": [self._serialize_chart(c) for c in charts],
            "insights": insights,
            "suggestions": suggestions,
            "processing_time_ms": processing_time
        }
    
    async def get_session_with_messages(
        self,
        session_id: UUID,
        user_id: UUID,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get session with messages"""
        session = self.db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if not session:
            raise ValueError("Session not found")
        
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).limit(limit).all()
        
        return {
            "session": session,
            "messages": messages,
            "message_count": len(messages)
        }
    
    async def get_user_sessions(
        self,
        user_id: UUID,
        org_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get user's chat sessions"""
        query = self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.organization_id == org_id
        )
        
        total = query.count()
        sessions = query.order_by(
            desc(ChatSession.last_message_at)
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        # Add message counts
        for session in sessions:
            session.message_count = self.db.query(func.count(ChatMessage.id)).filter(
                ChatMessage.session_id == session.id
            ).scalar()
        
        return {
            "sessions": sessions,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    def get_quick_actions(self, data_source_id: Optional[UUID] = None) -> List[QuickActionResponse]:
        """Get quick action suggestions"""
        actions = [
            QuickActionResponse(
                label="Summary Dashboard",
                prompt="Create a summary dashboard with key metrics and trends",
                category="overview"
            ),
            QuickActionResponse(
                label="Trend Analysis",
                prompt="Show me trends over time for key metrics",
                category="time_series"
            ),
            QuickActionResponse(
                label="Top Performers",
                prompt="Show top 10 items by value",
                category="ranking"
            ),
            QuickActionResponse(
                label="Comparison View",
                prompt="Compare metrics across different categories",
                category="comparison"
            ),
        ]
        
        # Add data-source specific actions if available
        if data_source_id:
            ds = self.db.query(DataSource).filter(DataSource.id == data_source_id).first()
            if ds and ds.schema_metadata:
                # Add custom actions based on schema
                schema = ds.schema_metadata
                if schema.get('time_column'):
                    actions.append(QuickActionResponse(
                        label="Time Series Analysis",
                        prompt=f"Analyze trends in {schema.get('time_column')}",
                        category="time_series"
                    ))
        
        return actions
    
    # Private helper methods
    
    def _get_conversation_context(self, session_id: UUID, limit: int = 10) -> List[Dict]:
        """Get recent conversation messages"""
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(desc(ChatMessage.created_at)).limit(limit).all()
        
        return [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(messages)
        ]
    
    async def _analyze_intent(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Analyze user intent from message"""
        prompt = f"""Analyze this user message and determine their intent.

User Message: {message}

Recent Context:
{json.dumps(context[-3:], indent=2) if context else "No context"}

Determine the intent type:
- "dashboard_generation": User wants to create a new dashboard
- "refinement": User wants to modify/improve existing dashboard
- "question": User is asking a question about data or functionality
- "general": General conversation

Return JSON with:
{{
  "type": "<intent_type>",
  "confidence": 0.0-1.0,
  "parameters": {{}}  // Any extracted parameters
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            intent = json.loads(content)
            return intent
            
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return {"type": "general", "confidence": 0.5, "parameters": {}}
    
    async def _handle_dashboard_generation(
        self,
        session: ChatSession,
        user_message: str,
        intent: Dict,
        context: List[Dict]
    ) -> Dict[str, Any]:
        """Handle dashboard generation request"""
        if not session.data_source_id:
            return {
                "content": "I'd be happy to help create a dashboard! First, please select a data source you'd like to visualize.",
                "message_type": "text",
                "meta_data": {"needs_data_source": True}
            }
        
        # Will generate dashboard in separate call
        return {
            "content": "I'll analyze your data and create a dashboard. This will take a moment...",
            "message_type": "text",
            "meta_data": {
                "action_required": "generate_dashboard",
                "query": user_message
            }
        }
    
    async def _handle_dashboard_refinement(
        self,
        session: ChatSession,
        user_message: str,
        intent: Dict,
        context: List[Dict]
    ) -> Dict[str, Any]:
        """Handle dashboard refinement request"""
        # Get most recent dashboard from session
        recent_gen = self.db.query(DashboardGeneration).filter(
            DashboardGeneration.session_id == session.id
        ).order_by(desc(DashboardGeneration.created_at)).first()
        
        if not recent_gen:
            return {
                "content": "I don't see any dashboards from our conversation yet. Would you like me to create one?",
                "message_type": "text"
            }
        
        return {
            "content": f"I'll refine the dashboard based on your request: '{user_message}'",
            "message_type": "text",
            "meta_data": {
                "action_required": "refine_dashboard",
                "dashboard_id": str(recent_gen.dashboard_id),
                "query": user_message
            }
        }
    
    async def _handle_question(
        self,
        session: ChatSession,
        user_message: str,
        intent: Dict,
        context: List[Dict]
    ) -> Dict[str, Any]:
        """Handle data question"""
        prompt = f"""You are a helpful data analytics assistant. Answer the user's question based on the conversation context.

User Question: {user_message}

Context:
{json.dumps(context, indent=2)}

Provide a helpful, concise answer. If you need more information or access to specific data, ask for it."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                "content": response.content[0].text,
                "message_type": "text",
                "token_count": response.usage.input_tokens + response.usage.output_tokens
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "content": "I apologize, but I encountered an error. Please try again.",
                "message_type": "text"
            }
    
    async def _handle_general_response(
        self,
        session: ChatSession,
        user_message: str,
        context: List[Dict]
    ) -> Dict[str, Any]:
        """Handle general conversation"""
        return await self._handle_question(session, user_message, {}, context)
    
    def _generate_session_title(self, first_message: str) -> str:
        """Generate a title from the first message"""
        title = first_message[:50]
        if len(first_message) > 50:
            title += "..."
        return title
    
    async def _load_data_source(self, data_source: DataSource) -> tuple:
        """Load data from data source"""
        # This should use the existing data loading logic
        # For now, placeholder - should integrate with actual data loading service
        from app.services.data_ingestion.csv_reader import CSVReader
        
        if data_source.type.value == "csv":
            reader = CSVReader()
            df = await reader.read_data(data_source)
            schema = data_source.schema_metadata
            return df, schema
        
        raise NotImplementedError(f"Data source type {data_source.type} not yet supported")
    
    async def _generate_charts_for_query(
        self,
        query: str,
        df: pd.DataFrame,
        schema: Dict,
        insights: List[Dict]
    ) -> List[Dict]:
        """Generate chart configurations based on query"""
        # This should use intelligent chart selection
        # For now, return basic charts based on schema
        charts = []
        
        # Add a trend chart if time column exists
        if schema.get('time_column') and schema.get('metrics'):
            metric = list(schema['metrics'].keys())[0]
            charts.append({
                "type": "line",
                "title": f"{metric} Over Time",
                "config": {
                    "x_axis": schema['time_column'],
                    "y_axis": metric,
                    "aggregation": "sum"
                }
            })
        
        # Add summary metrics
        if schema.get('metrics'):
            for metric_name in list(schema['metrics'].keys())[:3]:
                charts.append({
                    "type": "metric",
                    "title": metric_name.replace('_', ' ').title(),
                    "config": {
                        "metric": metric_name,
                        "aggregation": "sum"
                    }
                })
        
        return charts
    
    async def _create_dashboard(
        self,
        session: ChatSession,
        name: str,
        charts: List[Dict],
        insights: List[Dict],
        query: str
    ) -> Dashboard:
        """Create a new dashboard"""
        dashboard = Dashboard(
            name=name,
            org_id=session.organization_id,
            created_by=session.user_id,
            generated_by_ai=True,
            generation_context={"query": query, "insights_count": len(insights)}
        )
        self.db.add(dashboard)
        self.db.flush()
        
        # Add widgets (charts)
        for idx, chart in enumerate(charts):
            widget = Widget(
                dashboard_id=dashboard.id,
                data_source_id=session.data_source_id,
                title=chart.get("title", f"Chart {idx + 1}"),
                type=chart.get("type", "line"),
                config=chart.get("config", {}),
                position_x=0,
                position_y=idx * 2,
                width=12,
                height=2
            )
            self.db.add(widget)
        
        self.db.flush()
        return dashboard
    
    async def _refine_dashboard(self, dashboard_id: UUID, new_charts: List[Dict]) -> Dashboard:
        """Refine existing dashboard"""
        dashboard = self.db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
        if not dashboard:
            raise ValueError("Dashboard not found")
        
        # Add new widgets
        max_y = self.db.query(func.max(Widget.position_y)).filter(
            Widget.dashboard_id == dashboard_id
        ).scalar() or 0
        
        for idx, chart in enumerate(new_charts):
            widget = Widget(
                dashboard_id=dashboard.id,
                data_source_id=dashboard.widgets[0].data_source_id if dashboard.widgets else None,
                title=chart.get("title", f"Chart {idx + 1}"),
                type=chart.get("type", "line"),
                config=chart.get("config", {}),
                position_x=0,
                position_y=max_y + idx + 1,
                width=12,
                height=2
            )
            self.db.add(widget)
        
        self.db.flush()
        return dashboard
    
    async def _generate_suggestions(
        self,
        query: str,
        insights: List[Dict],
        schema: Dict
    ) -> List[str]:
        """Generate follow-up suggestions"""
        suggestions = []
        
        # Based on insights
        if any(i.get("type") == "trend" for i in insights):
            suggestions.append("Would you like to see a deeper breakdown by category?")
        
        if schema.get('dimensions'):
            dim = list(schema['dimensions'].keys())[0]
            suggestions.append(f"Compare by {dim}")
        
        suggestions.append("Add filters to focus on specific data")
        suggestions.append("Export this dashboard")
        
        return suggestions[:3]
    
    def _generate_explanation(self, charts: List[Dict], insights: List[Dict]) -> str:
        """Generate explanation of what was created"""
        return f"I've created a dashboard with {len(charts)} visualizations based on {len(insights)} key insights from your data."
    
    def _serialize_chart(self, chart: Dict) -> Dict:
        """Serialize chart for response"""
        return chart
