"""Add task_intents table

Revision ID: 0002
Revises: 0001
Create Date: 2025-12-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create task_intents table
    op.create_table(
        'task_intents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Enum('APPROVED', 'COMPLETED', 'CANCELLED', name='taskintentStatus'), nullable=False),
        sa.Column('intent_text', sa.Text(), nullable=False),
        sa.Column('origin_chat_id', sa.String(), nullable=True),
        sa.Column('user_key', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on user_key for efficient filtering
    op.create_index('ix_task_intents_user_key', 'task_intents', ['user_key'])
    # Create index on created_at for efficient sorting
    op.create_index('ix_task_intents_created_at', 'task_intents', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_task_intents_created_at', table_name='task_intents')
    op.drop_index('ix_task_intents_user_key', table_name='task_intents')
    op.drop_table('task_intents')
