"""update widgets for ai dashboard generation

Revision ID: update_widgets_ai_001
Revises: chat_system_tables_001
Create Date: 2026-02-10 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'update_widgets_ai_001'
down_revision = 'chat_system_tables_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename 'config' to 'query_config' and add new fields
    op.alter_column('widgets', 'widget_type', 
                    existing_type=sa.String(50), 
                    nullable=False)
    
    # Add new columns for comprehensive AI dashboard support
    op.add_column('widgets', sa.Column('description', sa.Text, nullable=True))
    op.add_column('widgets', sa.Column('query_config', postgresql.JSONB, nullable=False, server_default='{}'))
    op.add_column('widgets', sa.Column('chart_config', postgresql.JSONB, nullable=False, server_default='{}'))
    op.add_column('widgets', sa.Column('data_mapping', postgresql.JSONB, nullable=False, server_default='{}'))
    op.add_column('widgets', sa.Column('generated_by_ai', sa.Boolean, nullable=False, server_default='false'))
    op.add_column('widgets', sa.Column('generation_prompt', sa.Text, nullable=True))
    op.add_column('widgets', sa.Column('ai_reasoning', sa.Text, nullable=True))
    op.add_column('widgets', sa.Column('cache_duration_seconds', sa.Integer, nullable=False, server_default='300'))
    op.add_column('widgets', sa.Column('last_data_fetch', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('widgets', sa.Column('cached_data', postgresql.JSONB, nullable=True))
    
    # Migrate existing 'config' column data to 'query_config' if 'config' column exists
    # This handles the case where widgets already exist
    op.execute("""
        UPDATE widgets 
        SET query_config = COALESCE(config, '{}')
        WHERE query_config = '{}'
    """)
    
    # Drop old config column if it exists separately
    # (Only if it exists as a separate column and not renamed)
    try:
        op.drop_column('widgets', 'config')
    except:
        pass  # Column might not exist or already renamed
    
    # Update dashboard_id foreign key to use CASCADE on delete
    op.drop_constraint('widgets_dashboard_id_fkey', 'widgets', type_='foreignkey')
    op.create_foreign_key(
        'widgets_dashboard_id_fkey',
        'widgets', 'dashboards',
        ['dashboard_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Update data_source_id foreign key to use SET NULL on delete
    op.drop_constraint('widgets_data_source_id_fkey', 'widgets', type_='foreignkey')
    op.create_foreign_key(
        'widgets_data_source_id_fkey',
        'widgets', 'data_sources',
        ['data_source_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create index for AI-generated widgets
    op.create_index(
        'idx_widgets_ai_generated',
        'widgets',
        ['generated_by_ai', 'created_at'],
        postgresql_where=sa.text('generated_by_ai = true')
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_widgets_ai_generated', table_name='widgets')
    
    # Restore old foreign key constraints
    op.drop_constraint('widgets_data_source_id_fkey', 'widgets', type_='foreignkey')
    op.create_foreign_key(
        'widgets_data_source_id_fkey',
        'widgets', 'data_sources',
        ['data_source_id'], ['id']
    )
    
    op.drop_constraint('widgets_dashboard_id_fkey', 'widgets', type_='foreignkey')
    op.create_foreign_key(
        'widgets_dashboard_id_fkey',
        'widgets', 'dashboards',
        ['dashboard_id'], ['id']
    )
    
    # Add back config column and migrate data
    op.add_column('widgets', sa.Column('config', postgresql.JSONB, server_default='{}'))
    op.execute("UPDATE widgets SET config = query_config")
    
    # Drop new columns
    op.drop_column('widgets', 'cached_data')
    op.drop_column('widgets', 'last_data_fetch')
    op.drop_column('widgets', 'cache_duration_seconds')
    op.drop_column('widgets', 'ai_reasoning')
    op.drop_column('widgets', 'generation_prompt')
    op.drop_column('widgets', 'generated_by_ai')
    op.drop_column('widgets', 'data_mapping')
    op.drop_column('widgets', 'chart_config')
    op.drop_column('widgets', 'query_config')
    op.drop_column('widgets', 'description')
