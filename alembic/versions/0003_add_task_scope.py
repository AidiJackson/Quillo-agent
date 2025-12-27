"""Add task scope fields

Revision ID: 0003
Revises: 0002
Create Date: 2025-12-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add scope fields to task_intents table
    op.add_column('task_intents', sa.Column('scope_will_do', sa.JSON(), nullable=True))
    op.add_column('task_intents', sa.Column('scope_wont_do', sa.JSON(), nullable=True))
    op.add_column('task_intents', sa.Column('scope_done_when', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('task_intents', 'scope_done_when')
    op.drop_column('task_intents', 'scope_wont_do')
    op.drop_column('task_intents', 'scope_will_do')
