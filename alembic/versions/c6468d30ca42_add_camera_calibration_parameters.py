"""Add camera calibration parameters

Revision ID: c6468d30ca42
Revises: eb6eba00ede4
Create Date: 2024-05-17 14:30:03.568438

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c6468d30ca42'
down_revision = 'eb6eba00ede4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add parent_mobile_device_id column to enable nesting relationships,
    # e.g. a headset user carrying a thermal camera.
    with op.batch_alter_table("mobile_devices", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("parent_mobile_device_id", sa.Uuid(), default=None, nullable=True), insert_after="token")

    table = op.create_table('cameras',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('mobile_device_id', sa.Uuid(), sa.ForeignKey('mobile_devices.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('width', sa.Integer(), server_default="0", nullable=False),
        sa.Column('height', sa.Integer(), server_default="0", nullable=False),
        sa.Column('fx', sa.Float(), server_default="0", nullable=False),
        sa.Column('fy', sa.Float(), server_default="0", nullable=False),
        sa.Column('cx', sa.Float(), server_default="0", nullable=False),
        sa.Column('cy', sa.Float(), server_default="0", nullable=False),
        sa.Column('k1', sa.Float(), server_default="0", nullable=False),
        sa.Column('k2', sa.Float(), server_default="0", nullable=False),
        sa.Column('p1', sa.Float(), server_default="0", nullable=False),
        sa.Column('p2', sa.Float(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('cameras')
    op.drop_column("mobile_devices", "parent_mobile_device_id")
