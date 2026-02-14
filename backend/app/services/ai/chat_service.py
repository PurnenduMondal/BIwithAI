import logging
import json
import time
import asyncio
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, func, select
import pandas as pd

from anthropic import Anthropic

from app.config import settings
from app.models.chat import ChatSession, ChatMessage, DashboardGeneration, DashboardTemplate
from app.models.dashboard import Dashboard
from app.models.widget import Widget
from app.models.data_source import DataSource
from app.services.ai.insight_generator import InsightGenerator
from app.services.ai.dashboard_generator import DashboardGenerator
from app.schemas.chat import QuickActionResponse

logger = logging.getLogger(__name__)


class DashboardChatService:
    """Service for AI-powered dashboard generation through chat"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        self.insight_generator = InsightGenerator()
        self.dashboard_generator = DashboardGenerator()
    
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
        await self.db.commit()
        await self.db.refresh(session)
        
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
        result = await self.db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one_or_none()
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
        await self.db.flush()
        
        # Get conversation context
        context = await self._get_conversation_context(session_id)
        
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
            session.title = await self._generate_session_title(user_message)
        
        await self.db.commit()
        await self.db.refresh(assistant_msg)
        
        logger.info(f"Generated response for session {session_id} in {processing_time}ms")
        
        return {
            "message": assistant_msg,
            "intent": intent,
            "processing_time_ms": processing_time,
            "widget_previews": response.get("widget_previews"),  # Pass through widget previews
            "dashboard_id": response.get("dashboard_id")  # Pass through dashboard ID
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
        result = await self.db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one_or_none()
        if not session or session.user_id != user_id:
            raise ValueError("Invalid session")
        
        # Get data source
        result = await self.db.execute(select(DataSource).where(DataSource.id == data_source_id))
        data_source = result.scalar_one_or_none()
        if not data_source:
            raise ValueError("Data source not found")
        
        # Load data (this should be optimized with caching)
        df, schema = await self._load_data_source(data_source)
        
        # Get conversation context for better generation
        context = await self._get_conversation_context(session_id)
        
        # Analyze intent
        intent = await self._analyze_intent(query, context)
        
        # Use DashboardGenerator for intelligent dashboard creation
        dashboard_config = await self.dashboard_generator.generate_dashboard_config(
            user_query=query,
            df=df,
            schema=schema,
            intent=intent,
            conversation_context=context
        )
        
        # Generate insights separately
        insights = await self.insight_generator.generate_insights(df, schema, query)
        
        # Generate insights separately
        insights = await self.insight_generator.generate_insights(df, schema, query)
        
        # Merge insights from both sources
        all_insights = dashboard_config.get('insights', []) + insights[:3]
        
        # Create or update dashboard
        if refinement and existing_dashboard_id:
            dashboard = await self._refine_dashboard_with_config(
                existing_dashboard_id,
                dashboard_config.get('widgets', [])
            )
        else:
            dashboard = await self._create_dashboard_from_config(
                session=session,
                config=dashboard_config,
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
        await self.db.commit()
        await self.db.refresh(generation)
        
        # Get suggestions from config or generate
        suggestions = dashboard_config.get('suggestions', [])
        if not suggestions:
            suggestions = await self._generate_suggestions(query, all_insights, schema)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"Generated dashboard {dashboard.id} in {processing_time}ms")
        
        return {
            "dashboard_id": dashboard.id,
            "generation_id": generation.id,
            "explanation": dashboard_config.get('dashboard', {}).get('description', self._generate_explanation(dashboard_config.get('widgets', []), all_insights)),
            "charts": dashboard_config.get('widgets', []),
            "insights": all_insights,
            "suggestions": suggestions[:3],
            "processing_time_ms": processing_time
        }
    
    async def get_session_with_messages(
        self,
        session_id: UUID,
        user_id: UUID,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get session with messages"""
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .where(ChatSession.user_id == user_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError("Session not found")
        
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        messages = result.scalars().all()
        
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
        # Get total count
        count_result = await self.db.execute(
            select(func.count(ChatSession.id))
            .where(ChatSession.user_id == user_id)
            .where(ChatSession.organization_id == org_id)
        )
        total = count_result.scalar()
        
        # Get sessions
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .where(ChatSession.organization_id == org_id)
            .order_by(desc(ChatSession.last_message_at).nulls_last(), desc(ChatSession.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        sessions = result.scalars().all()
        
        # Add message counts
        for session in sessions:
            count_result = await self.db.execute(
                select(func.count(ChatMessage.id))
                .where(ChatMessage.session_id == session.id)
            )
            session.message_count = count_result.scalar()
        
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
            # Note: This method is not async, but we need to query the DB
            # This should be refactored or the method should be made async
            # For now, we'll skip the data source specific actions
            # TODO: Make get_quick_actions async
            pass
        
        return actions
    
    async def get_quick_actions_async(self, data_source_id: Optional[UUID] = None) -> List[QuickActionResponse]:
        """Get quick action suggestions (async version)"""
        actions = self.get_quick_actions(data_source_id)
        
        if data_source_id:
            result = await self.db.execute(select(DataSource).where(DataSource.id == data_source_id))
            ds = result.scalar_one_or_none()
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
    
    async def _get_conversation_context(self, session_id: UUID, limit: int = 10) -> List[Dict]:
        """Get recent conversation messages"""
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
        )
        messages = result.scalars().all()
        
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
        """Handle dashboard generation request - creates widgets immediately with preview"""
        if not session.data_source_id:
            return {
                "content": "I'd be happy to help create a dashboard! First, please select a data source you'd like to visualize.",
                "message_type": "text",
                "meta_data": {"needs_data_source": True}
            }
        
        try:
            # Load data source
            result = await self.db.execute(
                select(DataSource).where(DataSource.id == session.data_source_id)
            )
            data_source = result.scalar_one_or_none()
            
            if not data_source:
                return {
                    "content": "Data source not found. Please select a valid data source.",
                    "message_type": "text"
                }
            
            # Load data
            df, schema = await self._load_data_source(data_source)
            
            # Generate dashboard config using AI
            dashboard_config = await self.dashboard_generator.generate_dashboard_config(
                user_query=user_message,
                df=df,
                schema=schema,
                intent=intent,
                conversation_context=context
            )
            
            # Create or get draft dashboard for this session
            dashboard = await self._get_or_create_draft_dashboard(session, user_message)
            
            # Create widgets from config
            widget_previews = []
            for widget_config in dashboard_config.get('widgets', []):
                # Create widget in DB
                widget = Widget(
                    dashboard_id=dashboard.id,
                    data_source_id=session.data_source_id,
                    title=widget_config.get('title', 'Untitled'),
                    description=widget_config.get('description'),
                    widget_type=widget_config.get('type', 'bar'),
                    query_config=widget_config.get('query_config', {}),
                    chart_config=widget_config.get('chart_config', {}),
                    position=widget_config.get('position', {"x": 0, "y": len(widget_previews) * 6, "w": 6, "h": 9}),
                    generated_by_ai=True,
                    generation_prompt=user_message,
                    ai_reasoning=widget_config.get('reasoning')
                )
                self.db.add(widget)
                await self.db.flush()
                await self.db.refresh(widget)
                
                # Get preview data by executing the widget query
                from app.services.query.query_executor import QueryExecutor
                query_executor = QueryExecutor()
                
                # Merge configs for execution
                merged_config = {
                    **(widget.query_config or {}),
                    **(widget.chart_config or {})
                }
                
                # Execute query to get preview data
                preview_result = await query_executor.execute_widget_query(
                    df=df,
                    config=merged_config,
                    widget_type=widget.widget_type
                )
                
                logger.info(f"Widget {widget.id} ({widget.widget_type}): merged_config={merged_config}")
                logger.info(f"Widget {widget.id}: preview_result={preview_result}")
                
                # Extract data from the result dict
                # For metric/gauge widgets, the entire result IS the data (contains 'value', 'metric', 'aggregation')
                # For other widgets, extract the 'data' key (contains array of records)
                if widget.widget_type in ['metric', 'gauge']:
                    preview_data = preview_result
                else:
                    preview_data = preview_result.get('data', [])
                
                logger.info(f"Widget {widget.id}: preview_data={preview_data}")
                
                widget_previews.append({
                    "widget": {
                        "id": str(widget.id),
                        "title": widget.title,
                        "description": widget.description,
                        "widget_type": widget.widget_type,
                        "query_config": widget.query_config,
                        "chart_config": widget.chart_config,
                        "position": widget.position,
                        "ai_reasoning": widget.ai_reasoning
                    },
                    "data": preview_data[:100] if isinstance(preview_data, list) else preview_data  # Limit to 100 rows for preview
                })
            
            await self.db.commit()
            
            # Generate explanation
            explanation = dashboard_config.get('dashboard', {}).get('description', 
                f"I've created {len(widget_previews)} visualization(s) based on your request. You can see the preview below.")
            
            return {
                "content": explanation,
                "message_type": "widget_preview",
                "meta_data": {
                    "dashboard_id": str(dashboard.id),
                    "widget_count": len(widget_previews),
                    "insights": dashboard_config.get('insights', [])
                },
                "widget_previews": widget_previews,
                "dashboard_id": dashboard.id
            }
            
        except Exception as e:
            logger.error(f"Error generating dashboard: {e}", exc_info=True)
            return {
                "content": f"I encountered an error while creating the visualization: {str(e)}. Please try rephrasing your request.",
                "message_type": "text",
                "meta_data": {"error": str(e)}
            }
    
    async def _handle_dashboard_refinement(
        self,
        session: ChatSession,
        user_message: str,
        intent: Dict,
        context: List[Dict]
    ) -> Dict[str, Any]:
        """Handle dashboard refinement request - treats it as a new dashboard generation"""
        # For now, treat refinement like a new dashboard generation with context
        # This ensures widgets are actually created and previewed
        return await self._handle_dashboard_generation(
            session=session,
            user_message=user_message,
            intent=intent,
            context=context
        )
    
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
    
    async def _generate_session_title(self, first_message: str) -> str:
        """Generate a concise title from the first message using AI"""
        try:
            # Use Claude to generate a short, descriptive title
            # Run the blocking Anthropic call in a thread pool
            def _generate_title():
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=50,
                    temperature=0.3,
                    messages=[
                        {
                            "role": "user",
                            "content": f"""Generate a concise 3-7 word title for a dashboard chat session based on this user request:

"{first_message}"

Requirements:
- 3-7 words maximum
- Descriptive and specific
- No quotation marks
- Title case
- Focus on the main intent (e.g., "Sales Analysis Dashboard", "Revenue Trend Analysis", "Top Products by Region")

Title:"""
                        }
                    ]
                )
                return response
            
            # Run in thread pool to avoid blocking
            response = await asyncio.to_thread(_generate_title)
            
            # Extract title from response
            title = response.content[0].text.strip()
            
            # Remove quotes if present
            title = title.strip('"\'')
            
            # Ensure it's not too long (backup validation)
            words = title.split()
            if len(words) > 7:
                title = ' '.join(words[:7])
            
            logger.info(f"Generated AI title: {title}")
            return title
            
        except Exception as e:
            # Fallback to truncation if AI call fails
            logger.warning(f"Failed to generate AI title, using fallback: {e}")
            title = first_message[:50]
            if len(first_message) > 50:
                title += "..."
            return title
    
    async def _load_data_source(self, data_source: DataSource) -> tuple:
        """Load data from data source"""
        from app.services.data_ingestion.csv_connector import CSVConnector
        from app.services.data_ingestion.database_connector import DatabaseConnector
        from app.utils.encryption import decrypt_dict
        
        # Decrypt connection config
        config = decrypt_dict(data_source.connection_config)
        
        if data_source.type.value == "csv":
            connector = CSVConnector(config)
            df = await connector.fetch_data()
            schema = data_source.schema_metadata
            return df, schema
        elif data_source.type.value in ["postgresql", "mysql"]:
            connector = DatabaseConnector(data_source.type.value, config)
            df = await connector.fetch_data()
            schema = data_source.schema_metadata
            return df, schema
        
        raise NotImplementedError(f"Data source type {data_source.type} not yet supported")
    
    async def _create_dashboard_from_config(
        self,
        session: ChatSession,
        config: Dict[str, Any],
        query: str
    ) -> Dashboard:
        """Create a new dashboard from AI-generated config"""
        dashboard_info = config.get('dashboard', {})
        
        dashboard = Dashboard(
            name=dashboard_info.get('name', f"AI: {query[:50]}"),
            description=dashboard_info.get('description'),
            org_id=session.organization_id,
            created_by=session.user_id,
            generated_by_ai=True,
            generation_context={
                "query": query,
                "widget_count": len(config.get('widgets', [])),
                "insight_count": len(config.get('insights', []))
            }
        )
        self.db.add(dashboard)
        await self.db.flush()
        
        # Add widgets from config
        for widget_config in config.get('widgets', []):
            widget = Widget(
                dashboard_id=dashboard.id,
                data_source_id=session.data_source_id,
                title=widget_config.get('title', 'Untitled'),
                description=widget_config.get('description'),
                widget_type=widget_config.get('type', 'line'),
                query_config=widget_config.get('query_config', {}),
                chart_config=widget_config.get('chart_config', {}),
                position=widget_config.get('position', {"x": 0, "y": 0, "w": 6, "h": 9}),
                generated_by_ai=True,
                generation_prompt=query,
                ai_reasoning=widget_config.get('reasoning')
            )
            self.db.add(widget)
        
        await self.db.flush()
        return dashboard
    
    async def _refine_dashboard_with_config(
        self,
        dashboard_id: UUID,
        new_widgets: List[Dict]
    ) -> Dashboard:
        """Refine existing dashboard with new widgets"""
        result = await self.db.execute(select(Dashboard).where(Dashboard.id == dashboard_id))
        dashboard = result.scalar_one_or_none()
        if not dashboard:
            raise ValueError("Dashboard not found")
        
        # Get max Y position from existing widgets
        max_y = 0
        for widget in dashboard.widgets:
            widget_y = widget.position.get('y', 0) + widget.position.get('h', 0)
            if widget_y > max_y:
                max_y = widget_y
        
        # Add new widgets
        for widget_config in new_widgets:
            position = widget_config.get('position', {})
            if not position or 'y' not in position:
                position = {"x": 0, "y": max_y, "w": 6, "h": 4}
                max_y += 4
            
            widget = Widget(
                dashboard_id=dashboard.id,
                data_source_id=dashboard.widgets[0].data_source_id if dashboard.widgets else None,
                title=widget_config.get('title', 'New Widget'),
                description=widget_config.get('description'),
                widget_type=widget_config.get('type', 'line'),
                query_config=widget_config.get('query_config', {}),
                chart_config=widget_config.get('chart_config', {}),
                position=position,
                generated_by_ai=True,
                ai_reasoning=widget_config.get('reasoning')
            )
            self.db.add(widget)
        
        await self.db.flush()
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
    
    def _generate_explanation(self, widgets: List[Dict], insights: List[Dict]) -> str:
        """Generate explanation of what was created"""
        return f"I've created a dashboard with {len(widgets)} visualizations based on {len(insights)} key insights from your data."
    
    async def _get_or_create_draft_dashboard(self, session: ChatSession, query: str) -> Dashboard:
        """Get or create a draft dashboard for the session"""
        # Check if session already has a draft dashboard
        result = await self.db.execute(
            select(DashboardGeneration)
            .where(DashboardGeneration.session_id == session.id)
            .order_by(desc(DashboardGeneration.created_at))
        )
        recent_gen = result.scalar_one_or_none()
        
        if recent_gen:
            result = await self.db.execute(
                select(Dashboard).where(Dashboard.id == recent_gen.dashboard_id)
            )
            dashboard = result.scalar_one_or_none()
            if dashboard:
                return dashboard
        
        # Create new draft dashboard
        dashboard = Dashboard(
            name=f"AI Draft: {query[:40]}",
            description=f"AI-generated dashboard from chat",
            org_id=session.organization_id,
            created_by=session.user_id,
            generated_by_ai=True,
            generation_context={"session_id": str(session.id), "query": query}
        )
        self.db.add(dashboard)
        await self.db.flush()
        await self.db.refresh(dashboard)
        
        # Track generation
        generation = DashboardGeneration(
            session_id=session.id,
            dashboard_id=dashboard.id,
            generation_prompt=query,
            is_refinement=False
        )
        self.db.add(generation)
        await self.db.flush()
        
        return dashboard
