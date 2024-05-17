import datetime
import uuid

from typing import List

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from .base import Base
from .cameras import Camera
from .device_poses import DevicePose


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

    incident_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("incidents.id", ondelete="CASCADE"))
    location_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("locations.id", ondelete="CASCADE"))
    mobile_device_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("mobile_devices.id"), nullable=True)
    tracking_session_id: Mapped[int] = mapped_column(sa.ForeignKey("tracking_sessions.id"), nullable=True)
    device_pose_id: Mapped[int] = mapped_column(sa.ForeignKey("device_poses.id"), nullable=True)
    queue_name: Mapped[str] = mapped_column(sa.ForeignKey("photo_queues.name"), default="created", nullable=True)

    priority: Mapped[int] = mapped_column(default=0)
    retention: Mapped[str] = mapped_column(default="auto")

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    expiration_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.max)

    annotations: Mapped[List['PhotoAnnotation']] = relationship(cascade="all, delete-orphan") # noqa: F821
    camera: Mapped[Camera] = relationship(foreign_keys=[mobile_device_id], primaryjoin="Camera.mobile_device_id==PhotoRecord.mobile_device_id")
    files: Mapped[List['PhotoFile']] = relationship(back_populates="record", cascade="all, delete-orphan") # noqa: F821
    pose: Mapped[DevicePose] = relationship(foreign_keys=[device_pose_id])
