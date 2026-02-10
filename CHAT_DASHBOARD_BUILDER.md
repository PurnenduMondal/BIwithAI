# AI Chat Dashboard Builder

A conversational interface for generating and refining dashboards using natural language powered by Claude AI.

## Overview

The Chat Dashboard Builder allows users to create data visualizations through natural conversation, making business intelligence accessible without requiring technical knowledge of charts, queries, or data structures.

## Architecture

### Database Schema (PostgreSQL)

#### Core Tables

1. **chat_sessions** - Tracks conversation sessions
   - Links to user, organization, and optional data source
   - Stores conversation metadata and status
   - Timestamps for session lifecycle management

2. **chat_messages** - Individual messages in conversations
   - Supports user, assistant, and system messages
   - Stores rich metadata (charts, insights, suggestions)
   - Tracks token usage and processing time
   - Full-text search enabled on content

3. **dashboard_generations** - Links dashboards to chat sessions
   - Tracks generation vs refinement
   - Supports feedback scoring (1-5)
   - Maintains parent-child relationships for refinements

4. **dashboard_templates** - Reusable patterns learned from usage
   - Pattern matching for common queries
   - Chart configurations and schema requirements
   - Success metrics and usage tracking

### Key Features

#### PostgreSQL-Specific Optimizations

- **JSONB columns** for flexible metadata storage
- **GIN indexes** for fast JSONB queries
- **Full-text search** on message content
- **Materialized views** for analytics (can be added)
- **Partitioning** support for large chat history
- **Listen/Notify** for real-time updates

#### Indexes
```sql
-- Fast user session lookup
idx_chat_sessions_user ON (user_id, last_message_at DESC)

-- Session search by org
idx_chat_sessions_org ON (organization_id, created_at DESC)

-- Message retrieval
idx_chat_messages_session ON (session_id, created_at ASC)

-- Metadata search
idx_chat_messages_metadata USING GIN(metadata jsonb_path_ops)

-- Full-text search
idx_chat_messages_content_fts USING GIN(to_tsvector('english', content))

-- Template pattern matching
idx_dashboard_templates_intent USING GIN(intent_patterns jsonb_path_ops)

-- AI dashboard filtering
idx_dashboards_ai_generated ON (generated_by_ai, created_at DESC) WHERE generated_by_ai = TRUE
```

## API Endpoints

### Base URL: `/api/v1/chat`

#### Session Management

```http
POST /sessions
```
Create a new chat session
```json
{
  "data_source_id": "uuid",
  "title": "Optional title",
  "initial_message": "Create a sales dashboard"
}
```

```http
GET /sessions
```
List user's chat sessions (paginated)

```http
GET /sessions/{session_id}
```
Get session with message history

```http
DELETE /sessions/{session_id}
```
Delete a session

```http
PATCH /sessions/{session_id}/archive
```
Archive a session

#### Messaging

```http
POST /sessions/{session_id}/messages
```
Send a message and get AI response
```json
{
  "content": "Show me sales trends",
  "context": []  // Optional previous messages
}
```

#### Dashboard Generation

```http
POST /generate
```
Generate dashboard from natural language
```json
{
  "data_source_id": "uuid",
  "query": "Create a summary dashboard with key metrics",
  "refinement": false,
  "existing_dashboard_id": null
}
```

Response:
```json
{
  "dashboard_id": "uuid",
  "generation_id": "uuid",
  "explanation": "I've created a dashboard with 3 visualizations...",
  "charts": [...],
  "insights": [...],
  "suggestions": [
    "Add regional breakdown",
    "Compare to previous period"
  ],
  "processing_time_ms": 1250
}
```

#### Feedback

```http
POST /generations/{generation_id}/feedback
```
Rate a dashboard generation (1-5)

#### Quick Actions

```http
GET /quick-actions?data_source_id=uuid
```
Get contextual quick action suggestions

#### Context

```http
GET /context/{session_id}
```
Get full context for chat UI (session, data source, recent dashboards)

## Service Layer

### DashboardChatService

Located at: `app/services/ai/chat_service.py`

#### Key Methods

- `create_session()` - Initialize new chat session
- `send_message()` - Process user message and generate response
- `generate_dashboard()` - Create/refine dashboard from query
- `get_session_with_messages()` - Retrieve conversation history
- `get_quick_actions()` - Generate contextual suggestions

#### AI Integration

Uses Claude (Anthropic) for:
- **Intent analysis** - Understanding what user wants
- **Dashboard generation** - Chart selection and configuration
- **Insight generation** - Data analysis and recommendations  
- **Conversational responses** - Natural dialogue

### Intent Types

The system recognizes four main intent types:

1. **dashboard_generation** - User wants to create new dashboard
2. **refinement** - User wants to modify existing dashboard
3. **question** - User has a question about data/features
4. **general** - General conversation

## Frontend Integration

See the design document for the complete UI implementation, but key components:

### ChatDashboardBuilder Component

```tsx
<ChatDashboardBuilder
  dataSourceId={dataSourceId}
  onDashboardCreate={handleDashboardCreate}
/>
```

#### Features
- Split-pane layout (chat + preview)
- Real-time message streaming
- Quick action buttons
- Dashboard preview
- Refinement suggestions
- Export and save options

### States
- Loading/generating
- Preview mode
- Refinement mode
- Error handling

## Usage Examples

### Example 1: Quick Dashboard

```
User: "Show me a summary of sales data"
AI: "I'll create a summary dashboard with key metrics..."
[Generates dashboard with:
  - Total sales metric
  - Sales trend line chart
  - Top products bar chart
  - Regional breakdown
]
AI: "Created dashboard with 4 visualizations. Would you like to:
  - Add a comparison to last year
  - Filter by region
  - Show customer segments"
```

### Example 2: Iterative Refinement

```
User: "Create sales dashboard"
AI: [Generates basic dashboard]

User: "Add regional comparison"
AI: [Adds regional breakdown chart]

User: "Make the trend chart bigger"
AI: [Adjusts layout]

User: "Show only last quarter"
AI: [Adds date filter]
```

### Example 3: Data Questions

```
User: "What was our best month?"
AI: "Based on the data, March had the highest sales at $125K,
     which was 23% above average. Would you like to see a
     detailed breakdown?"

User: "Yes, break it down by product"
AI: [Generates product performance chart for March]
```

## Migration

Run the migration to create all required tables:

```bash
cd backend
alembic upgrade head
```

This will:
- Create chat_sessions table
- Create chat_messages table
- Create dashboard_generations table
- Create dashboard_templates table
- Add AI columns to dashboards table
- Create all indexes and constraints
- Set up triggers for updated_at

## Configuration

Required environment variables:

```env
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

## Performance Considerations

### Caching

Implement caching for:
- Data source loads (use Redis/in-memory cache)
- Schema metadata
- Common query patterns
- Template matching

### Query Optimization

- Use connection pooling
- Implement query result pagination
- Cache frequently accessed sessions
- Use EXPLAIN ANALYZE for slow queries

### Scaling

- Partition chat_messages by created_at (monthly)
- Archive old sessions to cold storage
- Use read replicas for analytics
- Consider materialized views for dashboards

## Future Enhancements

1. **Streaming Responses** - Real-time message streaming
2. **Multi-turn Context** - Better conversation memory
3. **Template Learning** - Automatic template creation from usage
4. **Voice Input** - Speech-to-text integration
5. **Collaborative Chat** - Share sessions with team
6. **Export Chat** - Download conversation history
7. **Semantic Search** - Find similar past conversations
8. **Smart Suggestions** - ML-powered action recommendations

## Testing

Key areas to test:
- Session creation and management
- Message processing and AI responses
- Dashboard generation accuracy
- Refinement workflows
- Error handling
- Performance under load
- Concurrent user sessions

## Monitoring

Track these metrics:
- Session creation rate
- Average messages per session
- Dashboard generation success rate
- Average processing time
- Token usage
- User feedback scores
- Template usage patterns

## Security

- Authentication required for all endpoints
- Users can only access their own sessions
- Organization-level isolation
- Input sanitization on all messages
- Rate limiting on AI calls
- Token usage limits per user/org
