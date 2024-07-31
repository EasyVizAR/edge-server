"""Add map paths

Revision ID: 954810c934e3
Revises: e00c66e7b8b5
Create Date: 2024-07-31 14:32:49.886214

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '954810c934e3'
down_revision = 'e00c66e7b8b5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    table = op.create_table('map_paths',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('mobile_device_id', sa.Uuid(), sa.ForeignKey('mobile_devices.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('target_marker_id', sa.Integer(), sa.ForeignKey('map_markers.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=False),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('points', sa.JSON(), default=[], nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('map_paths')
