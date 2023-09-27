import datetime
import time
import uuid

from marshmallow import post_dump
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from typing import List

from server.resources.dataclasses import dataclass, field
from server.resources.db import Base, MigrationSchema
from server.resources.geometry import Box, Vector3f, Vector4f
from server.resources.jsonresource import JsonCollection, JsonResource


# DEPRECATED
ENORMOUS_POSITION_ERROR = 100000.0


# DEPRECATED
@dataclass
class Annotation:
    label:      str = field(default="object")
    confidence: float = field(default=0.0)
    boundary:   Box = field(default_factory=Box)

    position:   Vector3f = field(default=None,
                                 description="Predicted center position of the detected object")
    position_error: float = field(default=ENORMOUS_POSITION_ERROR,
                                    description="Predicted position error (meters)")


# DEPRECATED
@dataclass
class Detector:
    model_repo:     str
    model_name:     str

    engine_name:            str = field(default="")
    engine_version:         str = field(default="")

    # DEPRECATED use engine_name and engine_version instead
    torch_version:          str = field(default="")
    torchvision_version:    str = field(default="")

    cuda_enabled:           bool = field(default=False)

    preprocess_duration:    float = field(default=0.0)
    inference_duration:     float = field(default=0.0)
    nms_duration:           float = field(default=0.0) # DEPRECATED use postprocess_duration
    postprocess_duration:   float = field(default=0.0)


# DEPRECATED
@dataclass
class PhotoFile_dc:
    """
    deprecated
    """
    name:   str

    purpose:        str = field(default="photo",
                                description="Meaning of the data in the file (photo|annotated|depth|geometry|thermal|thumbnail)")

    content_type:   str = field(default=None,
                                description="File MIME type (detected during creation)")
    height:         int = field(default=None,
                                description="Photo height in pixels (detected during creation)")
    width:          int = field(default=None,
                                description="Photo width in pixels (detected during creation)")


# DEPRECATED
@dataclass
class PhotoModel(JsonResource):
    """
    A photo uploaded by a headset.

    Headsets may upload photos of the environment for various reasons including
    sharing information with other team members or for automatic detection of
    objects in the photo.

    This is easily done with a multi-step procedure:
    1. The headset creates a photo object (POST /photos) with metadata such as
    the file type and image size.
    2. The server responds with a unique URL (imageUrl) for the image.
    3. The headset uploads the image file to the specified location using the
    PUT method.

    The server sets the `ready` flag to true after the image has been uploaded.
    Worker processes such as an object detector may wait for the `ready` flag
    to be set to begin processing.

    The implementation also features an experimental new approach that allows
    an arbitrary number of files to be associated with one photo object. The
    idea is that there may be multiple related images from the same moment in
    time and view point. The primary image is the full resolution color image,
    but we may also have a depth image, a thermal image, a smaller thumbnail
    image, an image with detected objects annotated, and so on. The various
    types of images can be stored and accessed using the "file by name" API
    functions.
    """
    id:             str

    contentType:    str = field(default="image/jpeg",
                                description="File MIME type")
    imagePath:      str = field(default=None,
                                description="Path to file if present on the server")
    imageUrl:       str = field(default=None,
                                description="Either a fully-specified URL (https://...) or a local path on the server (/photos/...)")
    ready:          bool = field(default=False,
                                 description="Indicates imageUrl is valid and ready and presumably readable")
    status:         str = field(default="unknown",
                                description="Status of the image (created|ready|done)")
    priority:       int = field(default=0,
                                description="Priority for image processing, (suggested 1=real-time, 0=normal, -1=background)")

    height:         int = field(default=None)
    width:          int = field(default=None)

    retention:      str = field(default="auto",
                                description="Retention policy for the photo (auto|permanent|temporary)")

    created_by:         str = field(default=None,
                                    description="Headset ID that submitted the photo")
    camera_location_id: str = field(default=None,
                                    description="Location ID where the photo was taken")
    camera_position:    Vector3f = field(default=None,
                                         description="Position of the camera in world coordinates")
    camera_orientation: Vector4f = field(default=None,
                                         description="Orientation of the camera (quaternion)")
    related_feature_id: str = field(default=None,
                                    description="Associated feature ID (if set) for a marker on the map where the photo was taken")

    annotations:    List[Annotation] = field(default_factory=list)
    detector:       Detector = field(default=None,
                                     description="Information about the object detector that was used")

    files:          List[PhotoFile_dc] = field(default_factory=list,
                                            description="List of files associated with this photo")

    created:        float = field(default_factory=time.time)
    updated:        float = field(default_factory=time.time)

    def infer_missing_annotation_positions(self, inferred_position_error=10.0):
        """
        Update annotations with missing position information.

        This uses the camera position to make a very crude position prediction
        for object locations.
        """
        if self.camera_position is None or self.camera_orientation is None:
            return

        pos = self.camera_position
        rot = self.camera_orientation

        # This math finds the forward vector from the camera_orientation
        # quaternion and adds it to the position vector for the camera. In
        # other words, we predict the object location to be one meter in front
        # of the camera.
        x = pos.x + 2*(rot.x*rot.z + rot.w*rot.y)
        y = pos.y + 2*(rot.y*rot.z - rot.w*rot.x)
        z = pos.z + 1 - 2*(rot.x**2 + rot.y**2)

        for annotation in self.annotations:
            if annotation.position is None or annotation.position_error is None or annotation.position_error > inferred_position_error:
                annotation.position = Vector3f(x, y, z)
                annotation.position_error = inferred_position_error


class PhotoRecord(Base):
    """
    A record for one or more related images uploaded by a mobile device.

    Devices may upload photos of the environment for various reasons including
    sharing information with other team members or for automatic detection of
    objects in the photo.

    This is easily done with a multi-step procedure:
    1. The device creates a photo object (POST /photos) with metadata such as
    the file type and image size.
    2. The server responds with a unique ID and URL (imageUrl) for the image.
    3. The device uploads the image file to the specified location using the
    PUT method.

    An arbitrary number of files can be associated with one photo object.  The
    idea is that there may be multiple related images from approximately the
    same moment in time and same view point. The primary image is the full
    resolution color image, but we may also have a depth image, a thermal
    image, a smaller thumbnail image, an image with detected objects annotated,
    and so on. The various types of images can be stored and accessed using
    the "file by name" API functions.

    Additionally, there are processing queues for uploaded photos. A typical
    workflow is the following. When a photo record has been created but no
    images have been uploaded, it sits in the "created" queue. After a primary
    image has been uploaded, it moves to the "detection" queue, from which an
    object detection worker will process it. When that is done, it moves to the
    "done" queue. Other queues may be defined if the need arises.
    """
    __tablename__ = "photo_records"
    __allow_update__ = set(['queue_name', 'priority', 'retention'])

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    incident_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("incidents.id"))
    location_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("locations.id"))

    queue_name: Mapped[str] = mapped_column(default="created", nullable=True)
    mobile_device_id: Mapped[uuid.UUID] = mapped_column(nullable=True)
    tracking_session_id: Mapped[int] = mapped_column(nullable=True)
    device_pose_id: Mapped[int] = mapped_column(nullable=True)

    priority: Mapped[int] = mapped_column(default=0)
    retention: Mapped[str] = mapped_column(default="auto")

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    expiration_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.max)

    annotations: Mapped[List['PhotoAnnotation']] = relationship(cascade="all, delete-orphan")
    files: Mapped[List['PhotoFile']] = relationship(back_populates="record", cascade="all, delete-orphan")


class PhotoFile(Base):
    __tablename__ = "photo_files"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    photo_record_id: Mapped[int] = mapped_column(sa.ForeignKey(PhotoRecord.id))
    name: Mapped[str] = mapped_column()

    purpose: Mapped[str] = mapped_column(default="photo")
    content_type: Mapped[str] = mapped_column(default="image/png")
    height: Mapped[int] = mapped_column(default=0)
    width: Mapped[int] = mapped_column(default=0)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    record: Mapped[PhotoRecord] = relationship()


class PhotoQueue(Base):
    __tablename__ = "photo_queues"

    name: Mapped[str] = mapped_column(primary_key=True)
    next_queue_name: Mapped[str] = mapped_column(default="done")
    display_order: Mapped[int] = mapped_column(default=0)
    description: Mapped[str] = mapped_column(default="")


class PhotoAnnotation(Base):
    __tablename__ = "photo_annotations"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    photo_record_id: Mapped[int] = mapped_column(sa.ForeignKey(PhotoRecord.id))
    detection_task_id: Mapped[int] = mapped_column(sa.ForeignKey("detection_tasks.id"))

    label: Mapped[str] = mapped_column(default="unknown")
    confidence: Mapped[float] = mapped_column(default=0.0)

    boundary_left: Mapped[float] = mapped_column(default=0.0)
    boundary_top: Mapped[float] = mapped_column(default=0.0)
    boundary_width: Mapped[float] = mapped_column(default=0.0)
    boundary_height: Mapped[float] = mapped_column(default=0.0)
    boundary: Mapped[Box] = composite(boundary_left, boundary_top, boundary_width, boundary_height)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)


class DetectionTask(Base):
    __tablename__ = "detection_tasks"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    photo_record_id: Mapped[int] = mapped_column(sa.ForeignKey(PhotoRecord.id))

    model_family: Mapped[str] = mapped_column(default="")
    model_name: Mapped[str] = mapped_column(default="")
    engine_name: Mapped[str] = mapped_column(default="")
    engine_version: Mapped[str] = mapped_column(default="")
    cuda_enabled: Mapped[bool] = mapped_column(default=False)

    preprocess_duration: Mapped[float] = mapped_column(default=0.0)
    execution_duration: Mapped[float] = mapped_column(default=0.0)
    postprocess_duration: Mapped[float] = mapped_column(default=0.0)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)


class PhotoAnnotationSchema(MigrationSchema):
    class Meta:
        model = PhotoAnnotation
        load_instance = True

    label = auto_field()
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
    status = auto_field('queue_name')

    priority = auto_field(description="Processing priority (0=normal, 1=real time, -1=low priority")
    retention = auto_field(description="Photo retention policy (auto|permanent|temporary)")

    created_by = auto_field('mobile_device_id', description="Mobile device ID which captured the photo")
    camera_location_id = auto_field('location_id', description="Location ID where the photo was captured")

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
