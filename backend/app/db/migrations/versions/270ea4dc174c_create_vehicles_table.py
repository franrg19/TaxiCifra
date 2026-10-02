"""create vehicles table

Revision ID: 270ea4dc174c
Revises: d717906f9c4b
Create Date: 2026-10-02 14:56:44.303895

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '270ea4dc174c'
down_revision: str | None = 'd717906f9c4b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('vehicles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('plate', sa.String(length=15), nullable=False),
    sa.Column('brand', sa.String(length=50), nullable=False),
    sa.Column('model', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'plate', name='uq_vehicles_user_id_plate')
    )
    op.create_index(op.f('ix_vehicles_user_id'), 'vehicles', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_vehicles_user_id'), table_name='vehicles')
    op.drop_table('vehicles')
