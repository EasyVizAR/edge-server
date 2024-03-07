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

    id = auto_field()
    photo_record_id = auto_field()
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
    tracking_session_id = auto_field()

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


class PhotoQueueSchema(MigrationSchema):
    class Meta:
        model = PhotoQueue
        load_instance = True

    name = auto_field()
    next_queue_name = auto_field()
    display_order = auto_field()
    description = auto_field()


default_photo_queues = [
  {
    "description": "A photo record has been created, but the files have not been uploaded yet.",
    "display_order": 10,
    "name": "created",
    "next_queue_name": "detection"
  },
  {
    "description": "The photo will be processing by an object detection module.",
    "display_order": 20,
    "name": "detection",
    "next_queue_name": "done"
  },
  {
    "description": "The photo will be processed by a 3D object detector",
    "display_order": 23,
    "name": "detection-3d",
    "next_queue_name": "done"
  },
  {
    "description": "The photo will be processed by a face recognition module.",
    "display_order": 25,
    "name": "identification",
    "next_queue_name": "done"
  },
  {
    "description": "All photo processing has completed.",
    "display_order": 30,
    "name": "done",
    "next_queue_name": None
  }
]


async def initialize_photo_queues(app):
    existing_queues = set()

    async with app.session_maker() as session:
        stmt = sa.select(PhotoQueue).order_by(PhotoQueue.display_order)
        result = await session.execute(stmt)
        for row in result.scalars():
            existing_queues.add(row.name)

        for item in default_photo_queues:
            if item['name'] not in existing_queues:
                queue = PhotoQueue(**item)
                session.add(queue)
                await session.flush()

        await session.commit()
