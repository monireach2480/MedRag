"""add conversations messages admin

Revision ID: b9422c109aec
Revises: 
Create Date: 2026-06-07 09:23:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b9422c109aec'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create conversations table
    op.create_table('conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add is_admin column to users - handle existing rows
    # Step 1: Add column as nullable
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True))
    
    # Step 2: Set default value for existing rows (False for regular users)
    op.execute("UPDATE users SET is_admin = FALSE WHERE is_admin IS NULL")
    
    # Step 3: Make column non-nullable
    op.alter_column('users', 'is_admin', nullable=False)


def downgrade() -> None:
    op.drop_column('users', 'is_admin')
    op.drop_table('messages')
    op.drop_table('conversations')