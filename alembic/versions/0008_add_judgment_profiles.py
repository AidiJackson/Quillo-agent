"""Add judgment profiles table

Revision ID: 0008
Revises: 0007
Create Date: 2026-01-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create judgment_profiles table
    op.create_table(
        'judgment_profiles',
        sa.Column('user_key', sa.String(), nullable=False),
        sa.Column('profile_json', sa.Text(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('user_key'),
        sa.UniqueConstraint('user_key', name='uq_judgment_profile_user_key')
    )

    # Create index on user_key for fast lookups (redundant with PK but explicit)
    op.create_index(
        'ix_judgment_profiles_user_key',
        'judgment_profiles',
        ['user_key']
    )


def downgrade() -> None:
    op.drop_index('ix_judgment_profiles_user_key', table_name='judgment_profiles')
    op.drop_table('judgment_profiles')
