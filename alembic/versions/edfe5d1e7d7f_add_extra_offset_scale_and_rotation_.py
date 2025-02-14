"""Add extra offset, scale, and rotation fields

Revision ID: edfe5d1e7d7f
Revises: 9230955d5ab2
Create Date: 2025-02-14 13:09:28.028731

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'edfe5d1e7d7f'
down_revision = '9230955d5ab2'
branch_labels = None
depends_on = None



def upgrade() -> None:
    with op.batch_alter_table("device_configurations", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("enable_marker_placement", sa.Boolean(), default=True, nullable=False), insert_after="enable_gesture_recognition")

    with op.batch_alter_table("map_markers", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("scale_x", sa.Float(), default=1.0, nullable=False), insert_after="position_z")
        batch_op.add_column(sa.Column("scale_y", sa.Float(), default=1.0, nullable=False), insert_after="position_z")
        batch_op.add_column(sa.Column("scale_z", sa.Float(), default=1.0, nullable=False), insert_after="position_z")
        batch_op.add_column(sa.Column("orientation_x", sa.Float(), default=0.0, nullable=False), insert_after="position_z")
        batch_op.add_column(sa.Column("orientation_y", sa.Float(), default=0.0, nullable=False), insert_after="position_z")
        batch_op.add_column(sa.Column("orientation_z", sa.Float(), default=0.0, nullable=False), insert_after="position_z")
        batch_op.add_column(sa.Column("orientation_w", sa.Float(), default=1.0, nullable=False), insert_after="position_z")

    with op.batch_alter_table("mobile_devices", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("offset_x", sa.Float(), default=0.0, nullable=False), insert_after="navigation_target_id")
        batch_op.add_column(sa.Column("offset_y", sa.Float(), default=0.0, nullable=False), insert_after="navigation_target_id")
        batch_op.add_column(sa.Column("offset_z", sa.Float(), default=0.0, nullable=False), insert_after="navigation_target_id")
        batch_op.add_column(sa.Column("rotation_x", sa.Float(), default=0.0, nullable=False), insert_after="navigation_target_id")
        batch_op.add_column(sa.Column("rotation_y", sa.Float(), default=0.0, nullable=False), insert_after="navigation_target_id")
        batch_op.add_column(sa.Column("rotation_z", sa.Float(), default=0.0, nullable=False), insert_after="navigation_target_id")

def downgrade() -> None:
    op.drop_column("device_configurations", "enable_marker_placement")

    op.drop_column("map_markers", "scale_x")
    op.drop_column("map_markers", "scale_y")
    op.drop_column("map_markers", "scale_z")
    op.drop_column("map_markers", "orientation_x")
    op.drop_column("map_markers", "orientation_y")
    op.drop_column("map_markers", "orientation_z")
    op.drop_column("map_markers", "orientation_w")

    op.drop_column("mobile_devices", "offset_x")
    op.drop_column("mobile_devices", "offset_y")
    op.drop_column("mobile_devices", "offset_z")
    op.drop_column("mobile_devices", "rotation_x")
    op.drop_column("mobile_devices", "rotation_y")
    op.drop_column("mobile_devices", "rotation_z")
