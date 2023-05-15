"""Migrate pose-changes from JSON files

Revision ID: 446e765b97f6
Revises: 
Create Date: 2023-05-12 16:24:47.488723

"""
from alembic import op
import sqlalchemy as sa

from server.incidents.models import Incident
from server.resources.geometry import Vector3f, Vector4f


# revision identifiers, used by Alembic.
revision = '446e765b97f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    table = op.create_table('pose_changes',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('incident_id', sa.String(), nullable=False),
        sa.Column('headset_id', sa.String(), nullable=False),
        sa.Column('check_in_id', sa.Integer(), nullable=False),
        sa.Column('time', sa.Float(), nullable=False),
        sa.Column('position_x', sa.Float(), nullable=False),
        sa.Column('position_y', sa.Float(), nullable=False),
        sa.Column('position_z', sa.Float(), nullable=False),
        sa.Column('orientation_x', sa.Float(), nullable=False),
        sa.Column('orientation_y', sa.Float(), nullable=False),
        sa.Column('orientation_z', sa.Float(), nullable=False),
        sa.Column('orientation_w', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    for incident in Incident.find():
        for headset in incident.Headset.find():
            for checkin in headset.CheckIn.find():
                pose_changes = []
                for posechange in checkin.PoseChange.find():
                    pose_changes.append({
                        "incident_id": incident.id,
                        "headset_id": headset.id,
                        "check_in_id": checkin.id,
                        "time": posechange.time,
                        "position_x": posechange.position.x,
                        "position_y": posechange.position.y,
                        "position_z": posechange.position.z,
                        "orientation_x": posechange.orientation.x,
                        "orientation_y": posechange.orientation.y,
                        "orientation_z": posechange.orientation.z,
                        "orientation_w": posechange.orientation.w
                    })

                if len(pose_changes) > 0:
                    op.bulk_insert(table, pose_changes)


def downgrade() -> None:
    op.drop_table('pose_changes')
