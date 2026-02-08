"""convert_enums_to_varchar_with_values

Revision ID: 43c91c216fd1
Revises: 89c35a7736fa
Create Date: 2026-02-07 23:37:28.822499

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '43c91c216fd1'
down_revision: Union[str, None] = '89c35a7736fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert users.role from ENUM to VARCHAR with lowercase values
    op.add_column('users', sa.Column('role_temp', sa.String(50), nullable=True))
    op.execute("UPDATE users SET role_temp = LOWER(role::text)")
    op.alter_column('users', 'role_temp', nullable=False)
    op.drop_column('users', 'role')
    op.alter_column('users', 'role_temp', new_column_name='role')
    
    # Convert data_sources.type from ENUM to VARCHAR with lowercase values
    op.add_column('data_sources', sa.Column('type_temp', sa.String(50), nullable=True))
    op.execute("UPDATE data_sources SET type_temp = LOWER(type::text)")
    op.alter_column('data_sources', 'type_temp', nullable=False)
    op.drop_column('data_sources', 'type')
    op.alter_column('data_sources', 'type_temp', new_column_name='type')
    
    # Convert data_sources.status from ENUM to VARCHAR with lowercase values
    op.add_column('data_sources', sa.Column('status_temp', sa.String(50), nullable=True))
    op.execute("UPDATE data_sources SET status_temp = LOWER(status::text)")
    op.drop_column('data_sources', 'status')
    op.alter_column('data_sources', 'status_temp', new_column_name='status')
    
    # Convert data_sources.sync_frequency from ENUM to VARCHAR with lowercase values
    op.add_column('data_sources', sa.Column('sync_frequency_temp', sa.String(50), nullable=True))
    op.execute("UPDATE data_sources SET sync_frequency_temp = LOWER(sync_frequency::text)")
    op.drop_column('data_sources', 'sync_frequency')
    op.alter_column('data_sources', 'sync_frequency_temp', new_column_name='sync_frequency')
    
    # Drop the old PostgreSQL ENUM types
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS datasourcetype")
    op.execute("DROP TYPE IF EXISTS datasourcestatus")
    op.execute("DROP TYPE IF EXISTS syncfrequency")


def downgrade() -> None:
    # Recreate ENUM types
    op.execute("CREATE TYPE userrole AS ENUM ('ADMIN', 'ANALYST', 'VIEWER')")
    op.execute("CREATE TYPE datasourcetype AS ENUM ('CSV', 'POSTGRESQL', 'MYSQL', 'API', 'GOOGLE_SHEETS')")
    op.execute("CREATE TYPE datasourcestatus AS ENUM ('PENDING', 'ACTIVE', 'ERROR', 'SYNCING')")
    op.execute("CREATE TYPE syncfrequency AS ENUM ('MANUAL', 'HOURLY', 'DAILY', 'WEEKLY')")
    
    # Convert data_sources.sync_frequency back to ENUM
    op.add_column('data_sources', sa.Column('sync_frequency_temp', sa.Enum('MANUAL', 'HOURLY', 'DAILY', 'WEEKLY', name='syncfrequency'), nullable=True))
    op.execute("UPDATE data_sources SET sync_frequency_temp = UPPER(sync_frequency)::syncfrequency")
    op.drop_column('data_sources', 'sync_frequency')
    op.alter_column('data_sources', 'sync_frequency_temp', new_column_name='sync_frequency')
    
    # Convert data_sources.status back to ENUM
    op.add_column('data_sources', sa.Column('status_temp', sa.Enum('PENDING', 'ACTIVE', 'ERROR', 'SYNCING', name='datasourcestatus'), nullable=True))
    op.execute("UPDATE data_sources SET status_temp = UPPER(status)::datasourcestatus")
    op.drop_column('data_sources', 'status')
    op.alter_column('data_sources', 'status_temp', new_column_name='status')
    
    # Convert data_sources.type back to ENUM
    op.add_column('data_sources', sa.Column('type_temp', sa.Enum('CSV', 'POSTGRESQL', 'MYSQL', 'API', 'GOOGLE_SHEETS', name='datasourcetype'), nullable=True))
    op.execute("UPDATE data_sources SET type_temp = UPPER(type)::datasourcetype")
    op.alter_column('data_sources', 'type_temp', nullable=False)
    op.drop_column('data_sources', 'type')
    op.alter_column('data_sources', 'type_temp', new_column_name='type')
    
    # Convert users.role back to ENUM
    op.add_column('users', sa.Column('role_temp', sa.Enum('ADMIN', 'ANALYST', 'VIEWER', name='userrole'), nullable=True))
    op.execute("UPDATE users SET role_temp = UPPER(role)::userrole")
    op.alter_column('users', 'role_temp', nullable=False)
    op.drop_column('users', 'role')
    op.alter_column('users', 'role_temp', new_column_name='role')
