"""create tickets table

Revision ID: 8020c3fa7a8c
Revises: 270ea4dc174c
Create Date: 2026-10-07 14:35:40.827265

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '8020c3fa7a8c'
down_revision: str | None = '270ea4dc174c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('tickets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('vehicle_id', sa.Integer(), nullable=True),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('vendor', sa.String(length=100), nullable=True),
    sa.Column('category', sa.String(length=20), nullable=True),
    sa.Column('net_amount', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('vat', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('total', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('image_path', sa.String(length=255), nullable=True),
    sa.Column('ocr_text', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tickets_user_id_date', 'tickets', ['user_id', 'date'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_tickets_user_id_date', table_name='tickets')
    op.drop_table('tickets')
