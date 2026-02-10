"""add chat system tables

Revision ID: chat_system_tables_001
Revises: 89c35a7736fa
Create Date: 2026-02-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'chat_system_tables_001'
down_revision = '89c35a7736fa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create chat_sessions table
    op.create_table('chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('data_source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('data_sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('meta_data', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('last_message_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("status IN ('active', 'completed', 'archived')", name='valid_status')
    )
    
    # Create indexes for chat_sessions
    op.create_index('idx_chat_sessions_user', 'chat_sessions', ['user_id', 'last_message_at'])
    op.create_index('idx_chat_sessions_org', 'chat_sessions', ['organization_id', 'created_at'])
    
    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('message_type', sa.String(50), nullable=False, server_default='text'),
        sa.Column('meta_data', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('token_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('processing_time_ms', sa.Integer, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("role IN ('user', 'assistant', 'system')", name='valid_role')
    )
    
    # Create indexes for chat_messages
    op.create_index('idx_chat_messages_session', 'chat_messages', ['session_id', 'created_at'])
    op.create_index('idx_chat_messages_meta_data', 'chat_messages', ['meta_data'], postgresql_using='gin', postgresql_ops={'meta_data': 'jsonb_path_ops'})
    
    # Create full-text search index on message content
    op.execute("""
        CREATE INDEX idx_chat_messages_content_fts ON chat_messages 
        USING GIN(to_tsvector('english', content))
    """)
    
    # Create dashboard_templates table
    op.create_table('dashboard_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('intent_patterns', postgresql.JSONB, nullable=False),
        sa.Column('chart_configs', postgresql.JSONB, nullable=False),
        sa.Column('schema_requirements', postgresql.JSONB, nullable=True),
        sa.Column('usage_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('success_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('created_from_session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_public', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    
    # Create indexes for dashboard_templates
    op.create_index('idx_dashboard_templates_intent', 'dashboard_templates', ['intent_patterns'], postgresql_using='gin', postgresql_ops={'intent_patterns': 'jsonb_path_ops'})
    
    # Create dashboard_generations table
    op.create_table('dashboard_generations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dashboard_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('dashboards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_messages.id', ondelete='SET NULL'), nullable=True),
        sa.Column('generation_prompt', sa.Text, nullable=True),
        sa.Column('is_refinement', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('parent_generation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('dashboard_generations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('feedback_score', sa.Integer, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint('feedback_score IS NULL OR (feedback_score >= 1 AND feedback_score <= 5)', name='valid_feedback')
    )
    
    # Create indexes for dashboard_generations
    op.create_index('idx_dashboard_generations_session', 'dashboard_generations', ['session_id'])
    
    # Add AI generation columns to dashboards table
    op.add_column('dashboards', sa.Column('generated_by_ai', sa.Boolean, nullable=False, server_default='false'))
    op.add_column('dashboards', sa.Column('generation_context', postgresql.JSONB, nullable=False, server_default='{}'))
    op.add_column('dashboards', sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('dashboard_templates.id', ondelete='SET NULL'), nullable=True))
    
    # Create index for AI-generated dashboards
    op.execute("""
        CREATE INDEX idx_dashboards_ai_generated ON dashboards(generated_by_ai, created_at DESC) 
        WHERE generated_by_ai = TRUE
    """)
    
    # Create trigger for updated_at on chat_sessions
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_chat_sessions_updated_at 
        BEFORE UPDATE ON chat_sessions
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    
    op.execute("""
        CREATE TRIGGER update_dashboard_templates_updated_at 
        BEFORE UPDATE ON dashboard_templates
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_dashboard_templates_updated_at ON dashboard_templates')
    op.execute('DROP TRIGGER IF EXISTS update_chat_sessions_updated_at ON chat_sessions')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    
    # Drop indexes from dashboards
    op.execute('DROP INDEX IF EXISTS idx_dashboards_ai_generated')
    
    # Remove columns from dashboards
    op.drop_column('dashboards', 'template_id')
    op.drop_column('dashboards', 'generation_context')
    op.drop_column('dashboards', 'generated_by_ai')
    
    # Drop tables in reverse order
    op.drop_table('dashboard_generations')
    op.drop_table('dashboard_templates')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
