"""Rebuild tables for mariadb

Revision ID: c31c0586510f
Revises: 
Create Date: 2025-11-14 09:45:44.057639

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c31c0586510f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# VARCHAR maximum sizes
TYPE_SIZE = 16
NAME_SIZE = 32
TOKEN_SIZE = 32
DESC_SIZE = 256


def upgrade() -> None:
    table = op.create_table('pose_changes',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('incident_id', sa.Uuid(), nullable=False),
        sa.Column('headset_id', sa.Uuid(), nullable=False),
        sa.Column('check_in_id', sa.Integer(), nullable=False),
        sa.Column('time', sa.Float(), nullable=False),
        sa.Column('position_x', sa.Float(), nullable=False),
        sa.Column('position_y', sa.Float(), nullable=False),
        sa.Column('position_z', sa.Float(), nullable=False),
        sa.Column('orientation_x', sa.Float(), nullable=False),
        sa.Column('orientation_y', sa.Float(), nullable=False),
        sa.Column('orientation_z', sa.Float(), nullable=False),
        sa.Column('orientation_w', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    table = op.create_table('incidents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(NAME_SIZE), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    table = op.create_table('users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(NAME_SIZE), nullable=False),
        sa.Column('password', sa.String(DESC_SIZE), nullable=False),
        sa.Column('display_name', sa.String(NAME_SIZE), nullable=False),
        sa.Column('type', sa.String(TYPE_SIZE), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        if_not_exists=True
    )

    table = op.create_table('streams',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('token', sa.String(NAME_SIZE), nullable=False),
        sa.Column('description', sa.String(DESC_SIZE), nullable=False),
        sa.Column('publisher_addr', sa.String(DESC_SIZE), nullable=True),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
        if_not_exists=True
    )

    table = op.create_table('photo_queues',
        sa.Column('name', sa.String(NAME_SIZE), nullable=False),
        sa.Column('next_queue_name', sa.String(NAME_SIZE), sa.ForeignKey('photo_queues.name', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(DESC_SIZE), nullable=False),
        sa.PrimaryKeyConstraint('name'),
        if_not_exists=True
    )

    table = op.create_table('locations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column("last_color_source_id", sa.Integer(), default=None, nullable=True),
        sa.Column('name', sa.String(NAME_SIZE), nullable=False),
        sa.Column('description', sa.String(DESC_SIZE), nullable=False),
        sa.Column("model_version", sa.Integer(), default=0, nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    table = op.create_table('layers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(NAME_SIZE), nullable=False),
        sa.Column('type', sa.String(TYPE_SIZE), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('image_type', sa.String(TYPE_SIZE), nullable=False),
        sa.Column('boundary_left', sa.Float(), nullable=False),
        sa.Column('boundary_top', sa.Float(), nullable=False),
        sa.Column('boundary_width', sa.Float(), nullable=False),
        sa.Column('boundary_height', sa.Float(), nullable=False),
        sa.Column('reference_height', sa.Float(), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    table = op.create_table('mobile_devices',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(NAME_SIZE), nullable=False),
        sa.Column('type', sa.String(TYPE_SIZE), nullable=False),
        sa.Column('color', sa.String(TYPE_SIZE), nullable=False),
        sa.Column("token", sa.String(TOKEN_SIZE), default="NONE", nullable=False, unique=True),
        sa.Column("parent_mobile_device_id", sa.Uuid(), default=None, nullable=True),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('tracking_session_id', sa.Integer(), default=None, nullable=True),
        sa.Column('device_pose_id', sa.Integer(), default=None, nullable=True),
        sa.Column('navigation_target_id', sa.Integer(), default=None, nullable=True),
        sa.Column("offset_x", sa.Float(), default=0.0, nullable=False),
        sa.Column("offset_y", sa.Float(), default=0.0, nullable=False),
        sa.Column("offset_z", sa.Float(), default=0.0, nullable=False),
        sa.Column("rotation_x", sa.Float(), default=0.0, nullable=False),
        sa.Column("rotation_y", sa.Float(), default=0.0, nullable=False),
        sa.Column("rotation_z", sa.Float(), default=0.0, nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    table = op.create_table('tracking_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('mobile_device_id', sa.Uuid(), sa.ForeignKey('mobile_devices.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('incident_id', sa.Uuid(), sa.ForeignKey('incidents.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    table = op.create_table('device_poses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tracking_session_id', sa.Integer(), sa.ForeignKey('tracking_sessions.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('mobile_device_id', sa.Uuid(), sa.ForeignKey('mobile_devices.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('position_x', sa.Float(), nullable=False),
        sa.Column('position_y', sa.Float(), nullable=False),
        sa.Column('position_z', sa.Float(), nullable=False),
        sa.Column('orientation_x', sa.Float(), nullable=False),
        sa.Column('orientation_y', sa.Float(), nullable=False),
        sa.Column('orientation_z', sa.Float(), nullable=False),
        sa.Column('orientation_w', sa.Float(), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    table = op.create_table('device_configurations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=True),
        sa.Column('mobile_device_id', sa.Uuid(), sa.ForeignKey('mobile_devices.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=True),
        sa.Column('enable_mesh_capture', sa.Boolean(), nullable=True),
        sa.Column('enable_photo_capture', sa.Boolean(), nullable=True),
        sa.Column('enable_extended_capture', sa.Boolean(), nullable=True),
        sa.Column("photo_capture_mode", sa.String(TYPE_SIZE), default="off", nullable=False),
        sa.Column("photo_detection_threshold", sa.Float(), default=0.65, nullable=False),
        sa.Column("photo_target_interval", sa.Float(), default=5, nullable=False),
        sa.Column("enable_gesture_recognition", sa.Boolean(), default=False, nullable=False),
        sa.Column("enable_marker_placement", sa.Boolean(), default=True, nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    table = op.create_table('map_markers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('type', sa.String(TYPE_SIZE), nullable=False),
        sa.Column('name', sa.String(NAME_SIZE), nullable=False),
        sa.Column('color', sa.String(TYPE_SIZE), nullable=False),
        sa.Column("enabled", sa.Boolean, default=True, nullable=False),
        sa.Column('position_x', sa.Float(), nullable=False),
        sa.Column('position_y', sa.Float(), nullable=False),
        sa.Column('position_z', sa.Float(), nullable=False),
        sa.Column("scale_x", sa.Float(), default=1.0, nullable=False),
        sa.Column("scale_y", sa.Float(), default=1.0, nullable=False),
        sa.Column("scale_z", sa.Float(), default=1.0, nullable=False),
        sa.Column("orientation_x", sa.Float(), default=0.0, nullable=False),
        sa.Column("orientation_y", sa.Float(), default=0.0, nullable=False),
        sa.Column("orientation_z", sa.Float(), default=0.0, nullable=False),
        sa.Column("orientation_w", sa.Float(), default=1.0, nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    table = op.create_table('surfaces',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('mobile_device_id', sa.Uuid(), sa.ForeignKey('mobile_devices.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    table = op.create_table('photo_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('incident_id', sa.Uuid(), sa.ForeignKey('incidents.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('mobile_device_id', sa.Uuid(), sa.ForeignKey('mobile_devices.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('tracking_session_id', sa.Integer(), sa.ForeignKey('tracking_sessions.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('device_pose_id', sa.Integer(), sa.ForeignKey('device_poses.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('queue_name', sa.String(NAME_SIZE), sa.ForeignKey('photo_queues.name', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('retention', sa.String(TYPE_SIZE), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expiration_time', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    table = op.create_table('photo_files',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('photo_record_id', sa.Integer(), sa.ForeignKey('photo_records.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(NAME_SIZE), nullable=False),
        sa.Column('purpose', sa.String(TYPE_SIZE), nullable=False),
        sa.Column('content_type', sa.String(TYPE_SIZE), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('photo_record_id', 'name'),
        if_not_exists=True
    )

    table = op.create_table('detection_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('photo_record_id', sa.Integer(), sa.ForeignKey('photo_records.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('model_family', sa.String(NAME_SIZE), nullable=False),
        sa.Column('model_name', sa.String(NAME_SIZE), nullable=False),
        sa.Column('engine_name', sa.String(NAME_SIZE), nullable=False),
        sa.Column('engine_version', sa.String(NAME_SIZE), nullable=False),
        sa.Column('cuda_enabled', sa.Boolean(), nullable=False),
        sa.Column('preprocess_duration', sa.Float(), nullable=False),
        sa.Column('execution_duration', sa.Float(), nullable=False),
        sa.Column('postprocess_duration', sa.Float(), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    table = op.create_table('photo_annotations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('photo_record_id', sa.Integer(), sa.ForeignKey('photo_records.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('detection_task_id', sa.Integer(), sa.ForeignKey('detection_tasks.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column("identified_user_id", sa.Uuid(), nullable=True),
        sa.Column('label', sa.String(NAME_SIZE), nullable=False),
        sa.Column("sublabel", sa.String(NAME_SIZE), default="", nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('boundary_left', sa.Float(), nullable=False),
        sa.Column('boundary_top', sa.Float(), nullable=False),
        sa.Column('boundary_width', sa.Float(), nullable=False),
        sa.Column('boundary_height', sa.Float(), nullable=False),
        sa.Column("contour", sa.JSON(), default=[], nullable=False),
        sa.Column("projected_contour", sa.JSON(), default=[], nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    table = op.create_table('cameras',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('mobile_device_id', sa.Uuid(), sa.ForeignKey('mobile_devices.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(TYPE_SIZE), nullable=False),
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
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    table = op.create_table('map_paths',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('mobile_device_id', sa.Uuid(), sa.ForeignKey('mobile_devices.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('target_marker_id', sa.Integer(), sa.ForeignKey('map_markers.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('type', sa.String(TYPE_SIZE), nullable=False),
        sa.Column('color', sa.String(TYPE_SIZE), nullable=False),
        sa.Column('label', sa.String(NAME_SIZE), nullable=False),
        sa.Column('points', sa.JSON(), default=[], nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    op.create_foreign_key('fk_last_color_source_id', 'locations', 'photo_records', ['last_color_source_id'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    op.create_foreign_key('fk_tracking_session_id', 'mobile_devices', 'tracking_sessions', ['tracking_session_id'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    op.create_foreign_key('fk_device_pose_id', 'mobile_devices', 'device_poses', ['device_pose_id'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    op.create_foreign_key('fk_navigation_target_id', 'mobile_devices', 'map_markers', ['navigation_target_id'], ['id'], onupdate='CASCADE', ondelete='SET NULL')


def downgrade() -> None:
    try:
        op.drop_constraint('fk_last_color_source_id', 'locations', type_='foreignkey')
        op.drop_constraint('fk_tracking_session_id', 'mobile_devices', type_='foreignkey')
        op.drop_constraint('fk_device_pose_id', 'mobile_devices', type_='foreignkey')
        op.drop_constraint('fk_navigation_target_id', 'mobile_devices', type_='foreignkey')
    except:
        pass

    op.drop_table('streams', if_exists=True)
    op.drop_table('cameras', if_exists=True)
    op.drop_table('map_paths', if_exists=True)
    op.drop_table('photo_annotations', if_exists=True)
    op.drop_table('photo_files', if_exists=True)
    op.drop_table('detection_tasks', if_exists=True)
    op.drop_table('surfaces', if_exists=True)
    op.drop_table('layers', if_exists=True)
    op.drop_table('device_configurations', if_exists=True)
    op.drop_table('map_markers', if_exists=True)
    op.drop_table('photo_records', if_exists=True)
    op.drop_table('photo_queues', if_exists=True)
    op.drop_table('device_poses', if_exists=True)
    op.drop_table('tracking_sessions', if_exists=True)
    op.drop_table('mobile_devices', if_exists=True)
    op.drop_table('pose_changes', if_exists=True)
    op.drop_table('users', if_exists=True)
    op.drop_table('locations', if_exists=True)
    op.drop_table('incidents', if_exists=True)
