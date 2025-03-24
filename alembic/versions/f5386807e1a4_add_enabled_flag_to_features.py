"""Add enabled flag to features

Revision ID: f5386807e1a4
Revises: edfe5d1e7d7f
Create Date: 2025-03-24 16:21:21.673505

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5386807e1a4'
down_revision = 'edfe5d1e7d7f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("map_markers", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("enabled", sa.Boolean, default=True, nullable=False), insert_after="color")


def downgrade() -> None:
    op.drop_column("map_markers", "enabled")

