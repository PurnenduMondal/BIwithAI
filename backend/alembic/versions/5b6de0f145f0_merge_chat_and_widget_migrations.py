"""merge_chat_and_widget_migrations

Revision ID: 5b6de0f145f0
Revises: 43c91c216fd1, update_widgets_ai_001
Create Date: 2026-02-10 19:20:58.396084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b6de0f145f0'
down_revision: Union[str, None] = ('43c91c216fd1', 'update_widgets_ai_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
