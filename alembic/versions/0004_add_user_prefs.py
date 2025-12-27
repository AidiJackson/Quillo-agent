"""Add user preferences table

Revision ID: 0004
Revises: 0003
Create Date: 2025-12-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_prefs table
    op.create_table(
        'user_prefs',
        sa.Column('user_key', sa.String(), nullable=False),
        sa.Column('approval_mode', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('user_key')
    )


def downgrade() -> None:
    op.drop_table('user_prefs')
