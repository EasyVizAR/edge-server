import datetime
import time
import uuid

from marshmallow import post_dump
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from typing import List

from server.models.detection_tasks import DetectionTask
from server.models.photo_annotations import PhotoAnnotation
from server.models.photo_files import PhotoFile
from server.models.photo_queues import PhotoQueue
from server.models.photo_records import PhotoRecord
from server.resources.db import MigrationSchema
from server.resources.geometry import Box, Vector3f, Vector4f


class PhotoAnnotationSchema(MigrationSchema):
    class Meta:
        model = PhotoAnnotation
        load_instance = True

    identified_user_id = auto_field()

    label = auto_field()
    sublabel = auto_field()
    confidence = auto_field()

    boundary = Nested(Box.Schema, many=False)


class PhotoFileSchema(MigrationSchema):
    class Meta:
        model = PhotoFile
        load_instance = True

    name = auto_field()
    purpose = auto_field()
    content_type = auto_field()
    height = auto_field()
    width = auto_field()


class DetectionTaskSchema(MigrationSchema):
    class Meta:
        model = DetectionTask
        load_instance = True

    model_family = auto_field()
    model_name = auto_field()
    engine_name = auto_field()
    engine_version = auto_field()

    preprocess_duration = auto_field()
    execution_duration = auto_field()
    postprocess_duration = auto_field()


class PhotoSchema(MigrationSchema):
    __convert_isotime_fields__ = ['created', 'updated']

    class Meta:
        model = PhotoRecord
        load_instance = True

    id = auto_field(description="Photo record ID (int)")

    queue_name = auto_field(description="Current processing queue (created|detection|identification|done)")
    priority = auto_field(description="Processing priority (0=normal, 1=real time, -1=low priority")
    retention = auto_field(description="Photo retention policy (auto|permanent|temporary)")

    created_by = auto_field('mobile_device_id', description="Mobile device ID which captured the photo")
    camera_location_id = auto_field('location_id', description="Location ID where the photo was captured")

    device_pose_id = auto_field()

    created = auto_field('created_time', description="Time the photo was created")
    updated = auto_field('updated_time', description="Time the photo was last update")

    annotations = Nested(PhotoAnnotationSchema, many=True)
    files = Nested(PhotoFileSchema, many=True)

    @post_dump(pass_original=True)
    def add_image_url(self, data, original, **kwargs):
        """
        Add imageUrl field for older clients that expect this field.
        """
        data['imageUrl'] = '/photos/{}/image'.format(original.id)
        return data

    @post_dump(pass_original=True)
    def add_status(self, data, original, **kwargs):
        """
        Add status and ready fields for older clients that expect this field.
        """
        if original.queue_name == "created":
            data['ready'] = False
            data['status'] = "created"
        elif original.queue_name == "detection":
            data['ready'] = True
            data['status'] = "ready"
        elif original.queue_name == "done":
            data['ready'] = True
            data['status'] = "done"
        else:
            data['ready'] = True
            data['status'] = "error"
        return data

    @post_dump(pass_original=True)
    def add_camera_pose(self, data, original, **kwargs):
        """
        Add position and orientation of camera if known.
        """
        if original.has('pose') and original.pose is not None:
            data['camera_position'] = original.pose.position
            data['camera_orientation'] = original.pose.orientation
        return data
