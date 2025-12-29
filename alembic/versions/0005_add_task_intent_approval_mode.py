"""Add approval_mode to task_intents table

Revision ID: 0005
Revises: 0004
Create Date: 2025-12-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add approval_mode column to task_intents table with default 'plan_then_auto'
    op.add_column(
        'task_intents',
        sa.Column('approval_mode', sa.String(), nullable=False, server_default='plan_then_auto')
    )


def downgrade() -> None:
    op.drop_column('task_intents', 'approval_mode')
