"""Add Lead table

Revision ID: add_lead_table
Revises: 
Create Date: 2025-04-18 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import datetime as dt

# revision identifiers, used by Alembic.
revision = 'add_lead_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create Lead table
    op.create_table('lead',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('chatbot_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['chatbot_id'], ['chatbot.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop Lead table
    op.drop_table('lead')
