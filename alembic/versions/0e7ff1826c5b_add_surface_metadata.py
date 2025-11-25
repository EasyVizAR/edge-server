"""add surface metadata

Revision ID: 0e7ff1826c5b
Revises: a2c436b9cd33
Create Date: 2025-11-25 15:39:02.964198

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0e7ff1826c5b'
down_revision = 'a2c436b9cd33'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("surfaces", sa.Column("version", sa.Integer(), nullable=False, server_default='0'))
    op.add_column("surfaces", sa.Column("num_faces", sa.Integer(), nullable=False, server_default='0'))
    op.add_column("surfaces", sa.Column("num_vertices", sa.Integer(), nullable=False, server_default='0'))
    op.add_column("surfaces", sa.Column("boundary_left", sa.Float(), nullable=False, server_default='0'))
    op.add_column("surfaces", sa.Column("boundary_top", sa.Float(), nullable=False, server_default='0'))
    op.add_column("surfaces", sa.Column("boundary_width", sa.Float(), nullable=False, server_default='0'))
    op.add_column("surfaces", sa.Column("boundary_height", sa.Float(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column("surfaces", "version")
    op.drop_column("surfaces", "num_faces")
    op.drop_column("surfaces", "num_vertices")
    op.drop_column("surfaces", "boundary_left")
    op.drop_column("surfaces", "boundary_top")
    op.drop_column("surfaces", "boundary_width")
    op.drop_column("surfaces", "boundary_height")
