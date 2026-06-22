"""add is_admin column to users

Revision ID: add_is_admin_column
Revises: 
Create Date: 2026-06-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_is_admin_column'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_admin column to users - handle existing rows
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True))
    op.execute("UPDATE users SET is_admin = FALSE WHERE is_admin IS NULL")
    op.alter_column('users', 'is_admin', nullable=False, server_default='f')


def downgrade() -> None:
    op.drop_column('users', 'is_admin')