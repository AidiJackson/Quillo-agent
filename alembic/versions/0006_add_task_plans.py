"""Add task_plans table

Revision ID: 0006
Revises: 0005
Create Date: 2025-12-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create task_plans table
    op.create_table(
        'task_plans',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('task_intent_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('plan_steps', sa.JSON(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='draft'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_intent_id'], ['task_intents.id']),
        sa.UniqueConstraint('task_intent_id')
    )


def downgrade() -> None:
    op.drop_table('task_plans')
