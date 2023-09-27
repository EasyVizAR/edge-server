"""Migrate to data model v2

Revision ID: 682684a1c52c
Revises: 446e765b97f6
Create Date: 2023-09-26 12:13:02.110282

Tables created:

    detection_tasks
    device_configurations
    device_poses
    incidents
    layers
    locations
    map_markers
    mobile_devices
    photo_annotations
    photo_files
    photo_queues
    photo_records
    surfaces
    tracking_sessions
    users
"""

import datetime
import operator
import os
import shutil
import uuid

from alembic import op
import sqlalchemy as sa

from werkzeug.security import generate_password_hash

from server.headset.models import Headset
from server.incidents.models import IncidentLoader
from server.resources.geometry import Vector3f, Vector4f


# revision identifiers, used by Alembic.
revision = '682684a1c52c'
down_revision = '446e765b97f6'
branch_labels = None
depends_on = None


# Maximum time difference between photo and device_pose
photo_match_max_time_difference = 15


def none_as_zero(x):
    if x is None:
        return 0
    else:
        return x


def create_tables():
    created_tables = dict()

    table = op.create_table('incidents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.Column('updated_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    created_tables[table.name] = table

    table = op.create_table('mobile_devices',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('tracking_session_id', sa.Integer(), sa.ForeignKey('tracking_sessions.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('device_pose_id', sa.Integer(), sa.ForeignKey('device_poses.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('navigation_target_id', sa.Integer(), sa.ForeignKey('map_markers.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.Column('updated_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    created_tables[table.name] = table

    table = op.create_table('tracking_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('mobile_device_id', sa.Uuid(), sa.ForeignKey('mobile_devices.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('incident_id', sa.Uuid(), sa.ForeignKey('incidents.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.Column('updated_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    created_tables[table.name] = table

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
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    created_tables[table.name] = table

    table = op.create_table('locations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.Column('updated_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    created_tables[table.name] = table

    table = op.create_table('device_configurations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=True),
        sa.Column('mobile_device_id', sa.Uuid(), sa.ForeignKey('mobile_devices.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=True),
        sa.Column('enable_mesh_capture', sa.Boolean(), nullable=True),
        sa.Column('enable_photo_capture', sa.Boolean(), nullable=True),
        sa.Column('enable_extended_capture', sa.Boolean(), nullable=True),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.Column('updated_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    created_tables[table.name] = table

    table = op.create_table('layers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('image_type', sa.String(), nullable=False),
        sa.Column('boundary_left', sa.Float(), nullable=False),
        sa.Column('boundary_top', sa.Float(), nullable=False),
        sa.Column('boundary_width', sa.Float(), nullable=False),
        sa.Column('boundary_height', sa.Float(), nullable=False),
        sa.Column('reference_height', sa.Float(), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.Column('updated_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    created_tables[table.name] = table

    table = op.create_table('map_markers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=False),
        sa.Column('position_x', sa.Float(), nullable=False),
        sa.Column('position_y', sa.Float(), nullable=False),
        sa.Column('position_z', sa.Float(), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.Column('updated_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    created_tables[table.name] = table

    table = op.create_table('surfaces',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('mobile_device_id', sa.Uuid(), sa.ForeignKey('mobile_devices.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.Column('updated_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    created_tables[table.name] = table

    table = op.create_table('photo_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('incident_id', sa.Uuid(), sa.ForeignKey('incidents.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('locations.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('mobile_device_id', sa.Uuid(), sa.ForeignKey('mobile_devices.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('tracking_session_id', sa.Integer(), sa.ForeignKey('tracking_session.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('device_pose_id', sa.Integer(), sa.ForeignKey('device_poses.id', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('queue_name', sa.String(), sa.ForeignKey('queues.name', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('retention', sa.String(), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.Column('updated_time', sa.DateTime(), nullable=False),
        sa.Column('expiration_time', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    created_tables[table.name] = table

    table = op.create_table('photo_files',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('photo_record_id', sa.Integer(), sa.ForeignKey('photo_records.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('purpose', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.Column('updated_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('photo_record_id', 'name')
    )
    created_tables[table.name] = table

    table = op.create_table('photo_queues',
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('next_queue_name', sa.String(), sa.ForeignKey('photo_queues.name', onupdate='CASCADE', ondelete='SET NULL'), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('name')
    )
    created_tables[table.name] = table

    table = op.create_table('photo_annotations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('photo_record_id', sa.Integer(), sa.ForeignKey('photo_records.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('detection_task_id', sa.Integer(), sa.ForeignKey('detection_tasks.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('boundary_left', sa.Float(), nullable=False),
        sa.Column('boundary_top', sa.Float(), nullable=False),
        sa.Column('boundary_width', sa.Float(), nullable=False),
        sa.Column('boundary_height', sa.Float(), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    created_tables[table.name] = table

    table = op.create_table('detection_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('photo_record_id', sa.Integer(), sa.ForeignKey('photo_records.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False),
        sa.Column('model_family', sa.String(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('engine_name', sa.String(), nullable=False),
        sa.Column('engine_version', sa.String(), nullable=False),
        sa.Column('cuda_enabled', sa.Boolean(), nullable=False),
        sa.Column('preprocess_duration', sa.Float(), nullable=False),
        sa.Column('execution_duration', sa.Float(), nullable=False),
        sa.Column('postprocess_duration', sa.Float(), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    created_tables[table.name] = table

    table = op.create_table('users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.Column('updated_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    created_tables[table.name] = table

    return created_tables


def upgrade() -> None:
    conn = op.get_bind()

    locations_dir = os.path.join('data', 'locations')
    os.makedirs(locations_dir, exist_ok=True)

    tables = create_tables()

    photo_queues = []
    users = []
    incidents = []
    locations = []
    device_configurations = []
    map_markers = []
    layers = []
    surfaces = []
    photo_records = []
    photo_files = []
    device_poses = []
    detection_tasks = []
    photo_annotations = []
    mobile_devices = []
    tracking_sessions = []

    delete_pose_change_ids = []

    photo_queues.append({
        'name': 'created',
        'next_queue_name': 'detection',
        'display_order': 10,
        'description': 'A photo record has been created, but the files have not been uploaded yet.'
    })
    photo_queues.append({
        'name': 'detection',
        'next_queue_name': 'done',
        'display_order': 20,
        'description': 'The photo will be processing by an object detection module.'
    })
    photo_queues.append({
        'name': 'done',
        'next_queue_name': None,
        'display_order': 30,
        'description': 'All photo processing has completed.'
    })

    users.append({
        'id': uuid.uuid4(),
        'name': 'user',
        'password': generate_password_hash(''),
        'display_name': 'Default User',
        'type': 'user',
        'created_time': datetime.datetime.now(),
        'updated_time': datetime.datetime.now()
    })
    users.append({
        'id': uuid.uuid4(),
        'name': 'admin',
        'password': generate_password_hash('admin'),
        'display_name': 'Default Admin',
        'type': 'admin',
        'created_time': datetime.datetime.now(),
        'updated_time': datetime.datetime.now()
    })

    mobile_devices_by_id = dict()
    for headset in Headset.find():
        new_mobile_device = {
            'id': uuid.UUID(headset.id),
            'name': headset.name,
            'type': headset.type,
            'color': headset.color,
            'location_id': None,
            'tracking_session_id': None,
            'device_pose_id': None,
            'created_time': datetime.datetime.fromtimestamp(headset.created),
            'updated_time': datetime.datetime.fromtimestamp(headset.updated)
        }
        mobile_devices.append(new_mobile_device)
        mobile_devices_by_id[new_mobile_device['id']] = new_mobile_device

        try:
            new_mobile_device['location_id'] = uuid.UUID(headset.location_id)
        except:
            pass

    for incident in IncidentLoader.find():
        new_incident = {
            'id': uuid.UUID(incident.id),
            'name': incident.name,
            'created_time': datetime.datetime.fromtimestamp(incident.created),
            'updated_time': datetime.datetime.fromtimestamp(incident.created),
        }
        incidents.append(new_incident)

        for headset in incident.Headset.find():
            try:
                mobile_device = mobile_devices_by_id[uuid.UUID(headset.id)]
            except:
                print("Warning: skipping headset {} with missing entry".format(headset.id))
                continue

            # Check-in IDS may be corrupted or missing in the pose_changes tables.
            # Instead, infer the end times of checkins and search for pose changes
            # that were recorded between the start and end time.
            checkins = []
            for checkin in headset.CheckIn.find():
                checkins.append(checkin)
            checkins.sort(key=operator.attrgetter("start_time"))
            for i, checkin in enumerate(checkins):
                if i+1 < len(checkins):
                    checkin.end_time = checkins[i+1].start_time
                else:
                    checkin.end_time = float("inf")

            for checkin in checkins:
                new_tracking_session = {
                    'id': len(tracking_sessions) + 1,
                    'mobile_device_id': mobile_device['id'],
                    'incident_id': new_incident['id'],
                    'location_id': None,
                    'user_id': users[0]['id'],
                    'created_time': datetime.datetime.fromtimestamp(checkin.start_time),
                    'updated_time': datetime.datetime.fromtimestamp(checkin.start_time)
                }

                try:
                    new_tracking_session['location_id'] = uuid.UUID(checkin.location_id)
                except:
                    print("Warning: skipping check-in {} for headset {} with bad location_id ({})".format(checkin.id, headset.id, checkin.location_id))
                    continue

                # Try to find the last matching check in / tracking session ID.
                if mobile_device['location_id'] == new_tracking_session['location_id']:
                    mobile_device['tracking_session_id'] = new_tracking_session['id']

                tracking_sessions.append(new_tracking_session)

                query = sa.text('SELECT id,time,position_x,position_y,position_z,orientation_x,orientation_y,orientation_z,orientation_w FROM pose_changes WHERE incident_id="{}" AND headset_id="{}" AND time>="{}" AND time <"{}"'.format(incident.id, headset.id, checkin.start_time, checkin.end_time))
                res = conn.execute(query)
                for row in res.fetchall():
                    new_device_pose = {
                        'id': len(device_poses) + 1,
                        'tracking_session_id': new_tracking_session['id'],
                        'mobile_device_id': mobile_device['id'],
                        'position_x': row[2],
                        'position_y': row[3],
                        'position_z': row[4],
                        'orientation_x': row[5],
                        'orientation_y': row[6],
                        'orientation_z': row[7],
                        'orientation_w': row[8],
                        'created_time': datetime.datetime.fromtimestamp(row[1])
                    }
                    device_poses.append(new_device_pose)

                    # Try to find the last appropriate device pose ID
                    if mobile_device['location_id'] == new_tracking_session['location_id']:
                        mobile_device['device_pose_id'] = new_device_pose['id']

                    delete_pose_change_ids.append(row[0])

        for location in incident.Location.find():
            new_location = {
                'id': uuid.UUID(location.id),
                'name': location.name,
                'description': location.description,
                'created_time': datetime.datetime.fromtimestamp(location.last_surface_update),
                'updated_time': datetime.datetime.fromtimestamp(location.last_surface_update)
            }
            locations.append(new_location)

            new_device_configuration = {
                'location_id': new_location['id'],
                'mobile_device_id': None,
                'enable_mesh_capture': location.headset_configuration.enable_mesh_capture,
                'enable_photo_capture': location.headset_configuration.enable_mesh_capture,
                'enable_extended_capture': location.headset_configuration.enable_mesh_capture,
                'created_time': new_location['created_time'],
                'updated_time': new_location['created_time']
            }
            device_configurations.append(new_device_configuration)

            location_dir = os.path.join(locations_dir, new_location['id'].hex)
            os.makedirs(location_dir, exist_ok=True)

            src = os.path.join(location.get_dir(), 'model.obj')
            if os.path.exists(src):
                shutil.copy2(src, location_dir)

            if new_location['description'] is None:
                new_location['description'] = ""

            for feature in location.Feature.find():
                new_map_marker = {
                    'id': len(map_markers) + 1,
                    'location_id': new_location['id'],
                    'user_id': None,
                    'type': feature.type,
                    'name': feature.name,
                    'color': feature.color,
                    'position_x': feature.position.x,
                    'position_y': feature.position.y,
                    'position_z': feature.position.z,
                    'created_time': datetime.datetime.fromtimestamp(feature.created),
                    'updated_time': datetime.datetime.fromtimestamp(feature.updated)
                }
                map_markers.append(new_map_marker)

                if feature.createdBy in [None, ""]:
                    # Created by default admin user
                    new_map_marker['user_id'] = users[1]['id']
                else:
                    # Created by default headset user
                    new_map_marker['user_id'] = users[0]['id']

            location_dir = os.path.join(locations_dir, new_location['id'].hex)
            os.makedirs(location_dir, exist_ok=True)

            src = os.path.join(location.get_dir(), 'model.obj')
            if os.path.exists(src):
                shutil.copy2(src, location_dir)

            for layer in location.Layer.find():
                new_layer = {
                    'id': len(layers) + 1,
                    'location_id': new_location['id'],
                    'name': layer.name,
                    'type': layer.type,
                    'version': layer.version,
                    'image_type': layer.contentType,
                    'boundary_left': layer.viewBox.left,
                    'boundary_top': layer.viewBox.top,
                    'boundary_width': layer.viewBox.width,
                    'boundary_height': layer.viewBox.height,
                    'reference_height': layer.cutting_height,
                    'created_time': datetime.datetime.fromtimestamp(layer.created),
                    'updated_time': datetime.datetime.fromtimestamp(layer.updated)
                }
                layers.append(new_layer)

                layer_dir = os.path.join(location_dir, 'layers', '{:08x}'.format(new_layer['id']))
                if layer.imagePath is not None and os.path.exists(layer.imagePath):
                    os.makedirs(layer_dir, exist_ok=True)
                    ext = os.path.splitext(layer.imagePath)[-1]
                    shutil.copy2(layer.imagePath, os.path.join(layer_dir, 'image'+ext))

            for scene in location.Scene.find():
                pass

            surfaces_dir = os.path.join(location_dir, 'surfaces')
            os.makedirs(surfaces_dir, exist_ok=True)

            for surface in location.Surface.find():
                new_surface = {
                    'id': None,
                    'location_id': new_location['id'],
                    'mobile_device_id': None,
                    'created_time': datetime.datetime.fromtimestamp(surface.created),
                    'updated_time': datetime.datetime.fromtimestamp(surface.updated)
                }

                try:
                    new_surface['id'] = uuid.UUID(surface.id)
                except:
                    print("Warning: skipping surface with invalid UUID ({})".format(surface.id))
                    continue

                surfaces.append(new_surface)

                try:
                    new_surface['mobile_device_id'] = uuid.UUID(surface.uploadedBy)
                except:
                    pass

                src = os.path.join(surface.get_dir(), 'surface.ply')
                if os.path.exists(src):
                    dest = os.path.join(surfaces_dir, "{}.ply".format(new_surface['id'].hex))
                    shutil.copy2(src, dest)

        for photo in incident.Photo.find():
            new_photo_record = {
                'id': len(photo_records) + 1,
                'incident_id': None,
                'location_id': None,
                'queue_name': "done",
                'mobile_device_id': None,
                'tracking_session_id': None,
                'device_pose_id': None,
                'priority': photo.priority,
                'retention': photo.retention,
                'created_time': datetime.datetime.fromtimestamp(photo.created),
                'updated_time': datetime.datetime.fromtimestamp(photo.updated),
                'expiration_time': datetime.datetime.max
            }

            # Assume the last incident for migrating the photos
            new_photo_record['incident_id'] = incidents[-1]['id']

            try:
                new_photo_record['location_id'] = uuid.UUID(photo.camera_location_id)
            except:
                print("Warning: skipping photo {} with invalid location UUID ({})".format(photo.id, photo.camera_location_id))
                continue

            photo_records.append(new_photo_record)

            try:
                new_photo_record['mobile_device_id'] = uuid.UUID(photo.created_by)
            except:
                pass

            photo_dir = os.path.join(locations_dir, new_photo_record['location_id'].hex, 'photos', '{:08x}'.format(new_photo_record['id']))
            os.makedirs(photo_dir, exist_ok=True)

            for fname in os.listdir(photo.get_dir()):
                if fname == 'photo.json':
                    continue
                path = os.path.join(photo.get_dir(), fname)
                shutil.copy2(path, photo_dir)

            # Find the closest pose_change record based on time, and if it is
            # close enough, use the associated pose_change_id, and check_in_id.
            # There is a risk we introduce position error for the photo, but
            # older data was not very accuate anyway.
            if new_photo_record['mobile_device_id'] is not None:
                query = sa.text("""
                    SELECT id, check_in_id, abs(time-{}) as tdiff
                    FROM pose_changes
                    WHERE headset_id="{}"
                    ORDER BY tdiff
                    LIMIT 1
                """.format(photo.created, photo.created_by))
                res = conn.execute(query)
                result = res.fetchone()

                if result is not None and result[2] < photo_match_max_time_difference:
                    new_photo_record['device_pose_id'] = result[0]
                    new_photo_record['tracking_session_id'] = result[1]

            for file in photo.files:
                new_photo_file = {
                    'id': len(photo_files) + 1,
                    'name': file.name,
                    'photo_record_id': new_photo_record['id'],
                    'purpose': file.purpose,
                    'content_type': file.content_type,
                    'height': file.height,
                    'width': file.width,
                    'created_time': new_photo_record['created_time'],
                    'updated_time': new_photo_record['updated_time']
                }
                photo_files.append(new_photo_file)

            if photo.detector is not None:
                new_detection_task = {
                    'id': len(detection_tasks) + 1,
                    'photo_record_id': new_photo_record['id'],
                    'model_family': photo.detector.model_repo,
                    'model_name': photo.detector.model_name,
                    'engine_name': photo.detector.engine_name,
                    'engine_version': photo.detector.engine_version,
                    'cuda_enabled': photo.detector.cuda_enabled,
                    'preprocess_duration': photo.detector.preprocess_duration,
                    'execution_duration': photo.detector.inference_duration,
                    'postprocess_duration': photo.detector.postprocess_duration,
                    'created_time': new_photo_record['updated_time']
                }
                detection_tasks.append(new_detection_task)

                if new_detection_task['engine_name'] in [None, ""] and photo.detector.torch_version not in [None, ""]:
                    new_detection_task['engine_name'] = "torch"
                    new_detection_task['engine_version'] = photo.detector.torch_version

                if photo.detector.nms_duration > photo.detector.postprocess_duration:
                    new_detection_task['postprocess_duration'] = photo.detector.nms_duration

                for annotation in photo.annotations:
                    new_photo_annotation = {
                        'id': len(photo_annotations) + 1,
                        'photo_record_id': new_photo_record['id'],
                        'detection_task_id': detection_tasks[-1]['id'],
                        'label': annotation.label,
                        'confidence': annotation.confidence,
                        'boundary_left': annotation.boundary.left,
                        'boundary_top': annotation.boundary.top,
                        'boundary_width': annotation.boundary.width,
                        'boundary_height': annotation.boundary.height,
                        'created_time': new_photo_record['updated_time']
                    }
                    photo_annotations.append(new_photo_annotation)

    op.bulk_insert(tables['photo_queues'], photo_queues)
    op.bulk_insert(tables['users'], users)
    op.bulk_insert(tables['incidents'], incidents)
    op.bulk_insert(tables['locations'], locations)
    op.bulk_insert(tables['device_configurations'], device_configurations)
    op.bulk_insert(tables['map_markers'], map_markers)
    op.bulk_insert(tables['layers'], layers)
    op.bulk_insert(tables['surfaces'], surfaces)
    op.bulk_insert(tables['photo_records'], photo_records)
    op.bulk_insert(tables['photo_files'], photo_files)
    op.bulk_insert(tables['device_poses'], device_poses)
    op.bulk_insert(tables['detection_tasks'], detection_tasks)
    op.bulk_insert(tables['photo_annotations'], photo_annotations)
    op.bulk_insert(tables['mobile_devices'], mobile_devices)
    op.bulk_insert(tables['tracking_sessions'], tracking_sessions)

    # Delete any pose_change rows that were migrated to device_poses.  Much of
    # the remaining data in the pose_change table will be from headsets that
    # were deleted.
    for pcid in delete_pose_change_ids:
        op.execute(sa.text('DELETE FROM pose_changes WHERE id="{}"'.format(pcid)))


def downgrade() -> None:
    conn = op.get_bind()

    query = sa.text("""
        SELECT device_poses.id, incident_id, device_poses.mobile_device_id, tracking_session_id, strftime("%s", device_poses.created_time), position_x,position_y,position_z,orientation_x,orientation_y,orientation_z,orientation_w
        FROM device_poses
        JOIN tracking_sessions ON tracking_sessions.mobile_device_id=device_poses.mobile_device_id AND tracking_sessions.id=tracking_session_id
    """)
    res = conn.execute(query)

    pose_changes = []
    for row in res.fetchall():
        pose_changes.append({
            'id': row[0],
            'incident_id': str(uuid.UUID(row[1])),
            'headset_id': str(uuid.UUID(row[2])),
            'check_in_id': row[3],
            'time': row[4],
            'position_x': row[5],
            'position_y': row[6],
            'position_z': row[7],
            'orientation_x': row[8],
            'orientation_y': row[9],
            'orientation_z': row[10],
            'orientation_w': row[11]
        })

    meta = sa.MetaData()
    meta.reflect(bind=op.get_bind(), only=('pose_changes',))
    pose_changes_table = sa.Table('pose_changes', meta)
    op.bulk_insert(pose_changes_table, pose_changes)

    op.drop_table('incidents')
    op.drop_table('mobile_devices')
    op.drop_table('tracking_sessions')
    op.drop_table('device_poses')
    op.drop_table('device_configurations')
    op.drop_table('locations')
    op.drop_table('layers')
    op.drop_table('map_markers')
    op.drop_table('surfaces')
    op.drop_table('photo_records')
    op.drop_table('photo_files')
    op.drop_table('photo_queues')
    op.drop_table('photo_annotations')
    op.drop_table('detection_tasks')
    op.drop_table('users')
