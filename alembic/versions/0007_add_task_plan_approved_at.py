"""add task plan approved_at

Revision ID: 0007
Revises: 0006
Create Date: 2025-12-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add approved_at timestamp column to task_plans table"""
    op.add_column(
        'task_plans',
        sa.Column('approved_at', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    """Remove approved_at column from task_plans table"""
    op.drop_column('task_plans', 'approved_at')
