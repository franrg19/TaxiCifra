"""create odometer readings table

Revision ID: b3338189c2f5
Revises: e9515bdad029
Create Date: 2026-10-21 10:15:59.187521

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = 'b3338189c2f5'
down_revision: str | None = 'e9515bdad029'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('odometer_readings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('vehicle_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('odometer_km', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_odometer_readings_user_id'), 'odometer_readings', ['user_id'], unique=False)
    op.create_index('ix_odometer_readings_vehicle_id_date', 'odometer_readings', ['vehicle_id', 'date'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_odometer_readings_vehicle_id_date', table_name='odometer_readings')
    op.drop_index(op.f('ix_odometer_readings_user_id'), table_name='odometer_readings')
    op.drop_table('odometer_readings')
