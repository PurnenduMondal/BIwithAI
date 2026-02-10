# Chat Dashboard Builder - Quick Start

## Setup

### 1. Run Database Migration

```bash
cd backend
alembic upgrade head
```

### 2. Verify Tables Created

```bash
psql -d your_database -c "\dt chat_*"
psql -d your_database -c "\dt dashboard_*"
```

You should see:
- chat_sessions
- chat_messages
- dashboard_generations
- dashboard_templates

### 3. Test API Endpoints

```bash
# Create a session
curl -X POST http://localhost:8000/api/v1/chat/sessions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data_source_id": "YOUR_DATA_SOURCE_ID",
    "title": "Test Chat"
  }'

# Send a message
curl -X POST http://localhost:8000/api/v1/chat/sessions/SESSION_ID/messages \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Show me a summary dashboard"
  }'

# Generate dashboard
curl -X POST http://localhost:8000/api/v1/chat/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data_source_id": "YOUR_DATA_SOURCE_ID",
    "query": "Create a sales summary dashboard"
  }'
```

## Frontend Integration

### Basic Usage

```tsx
import { ChatDashboardBuilder } from '@/components/dashboard/ChatDashboardBuilder';

function MyPage() {
  const [dataSourceId] = useState('your-data-source-id');
  
  const handleDashboardCreate = (dashboard) => {
    console.log('Dashboard created:', dashboard);
    // Navigate to dashboard or show success
  };
  
  return (
    <ChatDashboardBuilder
      dataSourceId={dataSourceId}
      onDashboardCreate={handleDashboardCreate}
    />
  );
}
```

### API Client Functions

Add to `frontend/src/api/chat.ts`:

```typescript
import { apiClient } from './client';

export const chatAPI = {
  createSession: async (dataSourceId?: string) => {
    return apiClient.post('/chat/sessions', { data_source_id: dataSourceId });
  },
  
  getSessions: async (page = 1, pageSize = 20) => {
    return apiClient.get('/chat/sessions', { params: { page, page_size: pageSize } });
  },
  
  getSession: async (sessionId: string) => {
    return apiClient.get(`/chat/sessions/${sessionId}`);
  },
  
  sendMessage: async (sessionId: string, content: string) => {
    return apiClient.post(`/chat/sessions/${sessionId}/messages`, { content });
  },
  
  generateDashboard: async (data: {
    data_source_id: string;
    query: string;
    refinement?: boolean;
    existing_dashboard_id?: string;
  }) => {
    return apiClient.post('/chat/generate', data);
  },
  
  submitFeedback: async (generationId: string, score: number) => {
    return apiClient.post(`/chat/generations/${generationId}/feedback`, {
      generation_id: generationId,
      feedback_score: score
    });
  },
  
  getQuickActions: async (dataSourceId?: string) => {
    return apiClient.get('/chat/quick-actions', {
      params: { data_source_id: dataSourceId }
    });
  }
};
```

## Key Files Created

### Backend
- `backend/app/models/chat.py` - Database models
- `backend/app/schemas/chat.py` - Pydantic schemas
- `backend/app/services/ai/chat_service.py` - Business logic
- `backend/app/api/v1/chat.py` - API endpoints
- `backend/alembic/versions/chat_system_tables_001.py` - Migration

### Frontend (To be created)
- `frontend/src/components/dashboard/ChatDashboardBuilder.tsx` - Main component
- `frontend/src/api/chat.ts` - API client
- `frontend/src/types/chat.ts` - TypeScript types

## Common Operations

### Check Session Status

```sql
SELECT 
  cs.id,
  cs.title,
  cs.status,
  COUNT(cm.id) as message_count,
  COUNT(DISTINCT dg.dashboard_id) as dashboards_generated,
  cs.last_message_at
FROM chat_sessions cs
LEFT JOIN chat_messages cm ON cs.id = cm.session_id
LEFT JOIN dashboard_generations dg ON cs.id = dg.session_id
WHERE cs.user_id = 'USER_ID'
GROUP BY cs.id
ORDER BY cs.last_message_at DESC;
```

### Find Popular Queries

```sql
SELECT 
  cm.content,
  COUNT(*) as frequency,
  AVG(dg.feedback_score) as avg_rating
FROM chat_messages cm
JOIN dashboard_generations dg ON cm.session_id = dg.session_id
WHERE cm.role = 'user'
  AND cm.message_type = 'text'
GROUP BY cm.content
HAVING COUNT(*) > 1
ORDER BY frequency DESC
LIMIT 10;
```

### Dashboard Generation Success Rate

```sql
SELECT 
  COUNT(*) as total_generations,
  COUNT(CASE WHEN feedback_score >= 4 THEN 1 END) as successful,
  ROUND(COUNT(CASE WHEN feedback_score >= 4 THEN 1 END)::numeric / COUNT(*)::numeric * 100, 2) as success_rate
FROM dashboard_generations
WHERE feedback_score IS NOT NULL;
```

## Debugging

### Enable Debug Logging

```python
import logging
logging.getLogger('app.services.ai.chat_service').setLevel(logging.DEBUG)
```

### Check Message Processing Time

```sql
SELECT 
  AVG(processing_time_ms) as avg_time,
  MIN(processing_time_ms) as min_time,
  MAX(processing_time_ms) as max_time,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_time_ms) as p95_time
FROM chat_messages
WHERE role = 'assistant'
  AND processing_time_ms IS NOT NULL;
```

### View Recent Errors

```sql
SELECT 
  cm.content,
  cm.metadata,
  cm.created_at
FROM chat_messages cm
WHERE cm.metadata->>'error' IS NOT NULL
ORDER BY cm.created_at DESC
LIMIT 10;
```

## Next Steps

1. **Test the migration** - Verify all tables and indexes created
2. **Test API endpoints** - Use curl or Postman
3. **Create frontend component** - Implement the UI design
4. **Add error handling** - Robust error messages
5. **Implement caching** - For data sources and schemas
6. **Add monitoring** - Track usage and performance
7. **Write tests** - Unit and integration tests

## Need Help?

- Check [CHAT_DASHBOARD_BUILDER.md](./CHAT_DASHBOARD_BUILDER.md) for full documentation
- Review the UI design mockup in the conversation history
- Look at existing API endpoints for patterns
- Test with small data sources first
