import datetime
import secrets
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from .base import Base
from .device_poses import DevicePose
from .map_markers import MapMarker


def generate_token():
    return secrets.token_urlsafe(16)


class MobileDevice(Base):
    replace_names = set(["Unity_Editor_Alieware", "ross_test"])
    valid_types = set(["unknown", "headset", "phone", "editor"])

    """
    Mobile devices are any individual devices that can be tracked and/or
    provide augmented reality visuals for the user.

    The most important fields are the name, position, and orientation. It is
    important for all devices involved in the same activity to synchronize to
    a common coordinate system so that the position and orientation can be
    meaningful.

    The device object tracks only the most recent position and orientation,
    together known as a "pose". The history of pose changes for a given device
    is stored separately in the pose-changes resource
    (/headset/{headset_id}/pose-changes).

    Events:

        headsets:created /headsets/<headset_id>
        headsets:updated /headsets/<headset_id>
        headsets:deleted /headsets/<headset_id>
        location-headsets:created /locations/<location_id>/headsets/<headset_id>
        location-headsets:updated /locations/<location_id>/headsets/<headset_id>
        location-headsets:deleted /locations/<location_id>/headsets/<headset_id>

    Websocket clients can subscribe to these events to receive notifications.
    Internal callers can use the event dispatcher (current_app.dispatcher).
    The headset:* events can be used to listen for any headsets or a specific
    headset. The location-headsets:* events can be used to filter for headset
    changes in a particular location.
    """
    __allow_update__ = set(['name', 'type', 'color', 'navigation_target_id'])
    __table_args__ = (
        sa.UniqueConstraint("token"),
    )
    __tablename__ = "mobile_devices"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(default="New Device")
    type: Mapped[str] = mapped_column(default="unknown")
    color: Mapped[str] = mapped_column(default="#4477aa")

    # Authentication token to be used by the device
    token: Mapped[str] = mapped_column(default=generate_token)

    location_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, sa.ForeignKey("locations.id"), nullable=True)
    tracking_session_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("tracking_sessions.id"), nullable=True)
    device_pose_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("device_poses.id"), nullable=True)
    navigation_target_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("map_markers.id"), nullable=True)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    pose: Mapped[DevicePose] = relationship(foreign_keys=[device_pose_id])
    navigation_target: Mapped[MapMarker] = relationship()
