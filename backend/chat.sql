-- Chat conversations for dashboard building
CREATE TABLE chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    data_source_id UUID NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active', -- active, archived, completed
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes for fast lookups
    INDEX idx_chat_conv_user (user_id, created_at DESC),
    INDEX idx_chat_conv_datasource (data_source_id),
    INDEX idx_chat_conv_status (status, updated_at DESC)
);

-- Chat messages with context
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text', -- text, dashboard_preview, chart_suggestion, insight
    
    -- Store structured data for AI context
    metadata JSONB DEFAULT '{}'::jsonb,
    -- metadata can contain:
    -- { "charts": [...], "insights": [...], "dashboard_id": "...", "intent": {...} }
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tokens_used INTEGER,
    
    -- Indexes
    INDEX idx_chat_msg_conv (conversation_id, created_at),
    INDEX idx_chat_msg_type (message_type, created_at DESC)
);

-- Dashboard generation history (link chat to generated dashboards)
CREATE TABLE dashboard_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE SET NULL,
    message_id UUID REFERENCES chat_messages(id) ON DELETE CASCADE,
    
    generation_prompt TEXT NOT NULL,
    generation_config JSONB NOT NULL, -- Charts, layouts, filters used
    
    is_active BOOLEAN DEFAULT true, -- Current version in conversation
    version INTEGER DEFAULT 1,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_dash_gen_conv (conversation_id, created_at DESC),
    INDEX idx_dash_gen_dashboard (dashboard_id),
    UNIQUE (conversation_id, version)
);

-- Quick action templates (reusable prompts)
CREATE TABLE quick_action_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    prompt_template TEXT NOT NULL,
    category VARCHAR(50), -- summary, trend, comparison, custom
    is_system BOOLEAN DEFAULT true,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    usage_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_templates_category (category, usage_count DESC),
    INDEX idx_templates_user (user_id, created_at DESC)
);

-- User preferences for chat behavior
CREATE TABLE user_chat_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    default_chart_types JSONB DEFAULT '["line", "bar", "pie"]'::jsonb,
    auto_generate_insights BOOLEAN DEFAULT true,
    conversation_history_limit INTEGER DEFAULT 50,
    preferred_data_sources UUID[],
    
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Full-text search for chat history
CREATE TABLE chat_search_index (
    message_id UUID PRIMARY KEY REFERENCES chat_messages(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    search_vector tsvector,
    
    INDEX idx_chat_search_vector USING gin(search_vector),
    INDEX idx_chat_search_user (user_id, conversation_id)
);

-- Trigger to update search index
CREATE OR REPLACE FUNCTION update_chat_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO chat_search_index (message_id, conversation_id, user_id, search_vector)
    SELECT 
        NEW.id,
        NEW.conversation_id,
        cc.user_id,
        to_tsvector('english', NEW.content)
    FROM chat_conversations cc
    WHERE cc.id = NEW.conversation_id
    ON CONFLICT (message_id)
    DO UPDATE SET search_vector = to_tsvector('english', NEW.content);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER chat_message_search_trigger
AFTER INSERT OR UPDATE OF content ON chat_messages
FOR EACH ROW
EXECUTE FUNCTION update_chat_search_vector();