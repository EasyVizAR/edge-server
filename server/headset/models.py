import datetime
import time
import uuid

from marshmallow import post_dump
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from server.feature.models import MapMarker
from server.pose_changes.models import DevicePose
from server.resources.dataclasses import dataclass, field
from server.resources.db import Base, MigrationSchema
from server.resources.jsonresource import JsonResource, JsonCollection
from server.resources.geometry import Vector3f, Vector4f


# DEPRECATED
@dataclass
class NavigationTarget:
    type:      str = field(default="none",
                           description="Target type (none|point|feature|headset)")
    target_id: str = field(default=None,
                           description="Target ID if type is feature or headset")
    position:  Vector3f = field(default_factory=Vector3f,
                                description="Fixed position for point type or last resolved position of feature or headset")


# DEPRECATED
@dataclass
class HeadsetModel(JsonResource):
    """
    Headset refers to any individual AR device that participates in the system.

    The most important fields are the name, position, and orientation. It is
    important for all headsets involved in the same activity to synchronize to
    a common coordinate system so that the position and orientation can be
    meaningful.

    The headset object tracks only the most recent position and orientation,
    together known as a "pose". The history of pose changes for a given headset
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
    id:     str
    name:   str = field(default="New Headset", description="Name of the headset")

    type:   str = field(default="unknown",
                        description="User device type (unknown|headset|phone|editor)")

    color:  str = field(default="#4477aa",
                        description="Suggested display color for the headset as a seven-character HTML color code.")

    location_id:    str = field(default=None,
                                description="Current location or NULL if unknown or inactive")
    last_check_in_id: int = field(default=None,
                                description="Most recent check-in or NULL if unknown")

    # mapId is deprecated and should be removed after transition to location and layer system
    mapId:  str = field(default=None, description="deprecated")

    position:       Vector3f = field(default_factory=Vector3f,
                                     description="Most recent position relative to current location")
    orientation:    Vector4f = field(default_factory=Vector4f,
                                     description="Most recent orientation relative to current location, represented as a quaternion")

    navigation_target: NavigationTarget = field(default=None,
                                                description="May be set to a NavigationTarget to provide navigation cues to the wearer")

    created:        float = field(default_factory=time.time)
    updated:        float = field(default_factory=time.time)


    def is_valid_spatial_sensor(self):
        """
        Check whether we can rely on this device for mapping data.

        Returns True for physical devices like headsets and False for
        testing or unknown devices.
        """
        return self.type in ["headset", "phone"]


# DEPRECATED
@dataclass
class RegisteredHeadsetModel(HeadsetModel):
    token: str = field(default=None, description="Authentication token")


# This is the top-level collection of headset data.  Import this and use
# Headset.find(), or other methods to query headsets, create headsets, and so
# on.
#
# DEPRECATED
Headset = JsonCollection(HeadsetModel, "headset", id_type="uuid")


class MobileDevice(Base):
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
    __tablename__ = "mobile_devices"
    __allow_update__ = set(['name', 'type', 'color', 'navigation_target_id'])

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(default="New Device")
    type: Mapped[str] = mapped_column(default="unknown")
    color: Mapped[str] = mapped_column(default="#4477aa")

    location_id: Mapped[uuid.UUID] = mapped_column(sa.UUID, sa.ForeignKey("locations.id"), nullable=True)
    tracking_session_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("tracking_sessions.id"), nullable=True)
    device_pose_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("device_poses.id"), nullable=True)
    navigation_target_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("map_markers.id"), nullable=True)

    pose: Mapped[DevicePose] = relationship(foreign_keys=[device_pose_id])
    navigation_target: Mapped[MapMarker] = relationship()

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)


class HeadsetSchema(MigrationSchema):
    __convert_isotime_fields__ = ['created', 'updated']

    class Meta:
        model = MobileDevice
        load_instance = True

    id = auto_field(description="Mobile device ID")

    name = auto_field(description="Name of the device")
    type = auto_field(description="Device type (unknown|headset|phone|editor)")
    color = auto_field(description="Suggested display color for the device as a seven-character HTML color code")

    location_id = auto_field(description="Current location ID or NULL if unknown or inactive")
    last_check_in_id = auto_field('tracking_session_id', description="Most recent tracking session ID or NULL if inactive")
    last_pose_change_id = auto_field('device_pose_id', description="Most recent device pose ID or NULL if unknown")
    navigation_target_id = auto_field(description="Navigation target of the device or NULL if unset")

    created = auto_field('created_time', description="Time the device was first registered")
    updated = auto_field('updated_time', description="Last time the device was updated")

    @post_dump(pass_original=True)
    def add_position_and_orientation(self, data, original, **kwargs):
        if original.pose is None:
            data['position'] = Vector3f()
            data['orientation'] = Vector4f()
        else:
            data['position'] = original.pose.position
            data['orientation'] = original.pose.orientation
        return data

    @post_dump(pass_original=True)
    def add_navigation_target(self, data, original, **kwargs):
        if original.has('navigation_target') and original.navigation_target is not None:
            data['navigation_target'] = {
                'type': 'feature',
                'target_id': original.navigation_target_id,
                'position': original.navigation_target.position
            }
        return data


class RegisteredHeadsetSchema(HeadsetSchema):
    token: str = field(default=None, description="Authentication token")
