"""Add model version and color source tracking to location

Revision ID: 9230955d5ab2
Revises: 954810c934e3
Create Date: 2025-01-09 13:08:46.877466

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9230955d5ab2'
down_revision = '954810c934e3'
branch_labels = None
depends_on = None



def upgrade() -> None:
    # First, add the columns
    with op.batch_alter_table("locations", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("last_color_source_id", sa.Integer, default=None, nullable=True), insert_after="id")
        batch_op.add_column(sa.Column("model_version", sa.Integer(), default=0, nullable=False), insert_after="description")
        batch_op.create_foreign_key("fk_last_color_source", "photo_records", ["last_color_source_id"], ["id"], ondelete="SET NULL", onupdate="CASCADE")


def downgrade() -> None:
    with op.batch_alter_table("locations", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_last_color_source", type_="foreignkey")
    op.drop_column("locations", "model_version")
    op.drop_column("locations", "last_color_source_id")
