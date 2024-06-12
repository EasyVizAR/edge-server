"""Add detected object contours

Revision ID: e00c66e7b8b5
Revises: c6468d30ca42
Create Date: 2024-06-12 13:12:46.303203

"""
import json

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e00c66e7b8b5'
down_revision = 'c6468d30ca42'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First, add the contour column.
    with op.batch_alter_table("photo_annotations", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("contour", sa.JSON(), default=[], nullable=False), insert_after="boundary_height")
        batch_op.add_column(sa.Column("projected_contour", sa.JSON(), default=[], nullable=False), insert_after="contour")

    # Then create a contour from existing bounding boxes
    conn = op.get_bind()
    query = sa.text('SELECT id, boundary_left, boundary_top, boundary_width, boundary_height FROM photo_annotations')
    res = conn.execute(query)
    for row in res.fetchall():
        id, left, top, width, height = row
        contour = [
            [left, top],
            [left, top + height],
            [left + width, top + height],
            [left + width, top],
            [left, top]
        ]
        op.execute('UPDATE photo_annotations SET contour="{}" WHERE id="{}"'.format(json.dumps(contour), id))


def downgrade() -> None:
    op.drop_column("photo_annotations", "projected_contour")
    op.drop_column("photo_annotations", "contour")
