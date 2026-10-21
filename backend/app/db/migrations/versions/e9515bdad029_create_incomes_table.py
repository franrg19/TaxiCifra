"""create incomes table

Revision ID: e9515bdad029
Revises: 8020c3fa7a8c
Create Date: 2026-10-21 09:43:35.210594

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = 'e9515bdad029'
down_revision: str | None = '8020c3fa7a8c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('incomes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('vehicle_id', sa.Integer(), nullable=True),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_incomes_user_id_date', 'incomes', ['user_id', 'date'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_incomes_user_id_date', table_name='incomes')
    op.drop_table('incomes')
