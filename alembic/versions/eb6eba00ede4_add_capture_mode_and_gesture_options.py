"""Add capture mode and gesture options

Revision ID: eb6eba00ede4
Revises: 9771ae035be9
Create Date: 2024-03-12 11:37:05.386380

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb6eba00ede4'
down_revision = '54180cada6b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("device_configurations", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("photo_capture_mode", sa.String(), default="off", nullable=False), insert_after="enable_extended_capture")
        batch_op.add_column(sa.Column("photo_detection_threshold", sa.Float(), default=0.65, nullable=False), insert_after="photo_capture_mode")
        batch_op.add_column(sa.Column("photo_target_interval", sa.Float(), default=5, nullable=False), insert_after="photo_detection_threshold")
        batch_op.add_column(sa.Column("enable_gesture_recognition", sa.Boolean(), default=False, nullable=False), insert_after="photo_capture_mode")


def downgrade() -> None:
    op.drop_column("device_configurations", "photo_capture_mode")
    op.drop_column("device_configurations", "photo_detection_threshold")
    op.drop_column("device_configurations", "photo_target_interval")
    op.drop_column("device_configurations", "enable_gesture_recognition")
