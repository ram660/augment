"""Add persona and scenario columns to conversations

Revision ID: 004
Revises: 003
Create Date: 2025-11-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to conversations table
    with op.batch_alter_table('conversations') as batch_op:
        batch_op.add_column(sa.Column('persona', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('scenario', sa.String(length=50), nullable=True))


def downgrade() -> None:
    # Remove columns from conversations table
    with op.batch_alter_table('conversations') as batch_op:
        batch_op.drop_column('scenario')
        batch_op.drop_column('persona')

