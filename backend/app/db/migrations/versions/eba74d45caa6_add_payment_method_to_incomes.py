"""add payment method to incomes

Revision ID: eba74d45caa6
Revises: b3338189c2f5
Create Date: 2026-11-07 16:48:29.799141

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = 'eba74d45caa6'
down_revision: str | None = 'b3338189c2f5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('incomes', sa.Column('payment_method', sa.String(length=10), nullable=True))


def downgrade() -> None:
    op.drop_column('incomes', 'payment_method')
