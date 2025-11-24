import datetime
import time
import uuid

from marshmallow import post_dump
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from server import messages_pb2
from server.feature.models import MapMarker
from server.models.mobile_devices import MobileDevice
from server.pose_changes.models import DevicePose
from server.resources.dataclasses import field
from server.resources.db import MigrationSchema
from server.resources.geometry import Vector3f, Vector4f


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

    offset = Nested(Vector3f.Schema, description="Position offset in world coordinates", many=False)
    rotation = Nested(Vector3f.Schema, description="Rotation from world coordinate system", many=False)

    created = auto_field('created_time', description="Time the device was first registered")
    updated = auto_field('updated_time', description="Last time the device was updated")

    @post_dump(pass_original=True)
    def add_position_and_orientation(self, data, original, **kwargs):
        if original.pose is None:
            data['position'] = -original.offset

            q = original.rotation.as_quaternion().inverse()
            data['orientation'] = Vector4f.from_quaternion(q)
        else:
            data['position'] = original.pose.position - original.offset
            data['orientation'] = original.pose.orientation.apply_rotation(-original.rotation)
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

    def to_protobuf(self):
        """
        Get protobuf message from object.
        """
        device = messages_pb2.Device()
        device.name = self.name
        device.color = self.color
        if self.location_id is not None:
            device.location_id = self.location_id.hex
        if self.navigation_target_id is not None:
            device.navigation_target_id = self.navigation_target_id
        device.position.x = self.position.x
        device.position.y = self.position.y
        device.position.z = self.position.z
        device.orientation.x = self.orientation.x
        device.orientation.y = self.orientation.y
        device.orientation.z = self.orientation.z
        device.orientation.w = self.orientation.w
        return device


class RegisteredHeadsetSchema(HeadsetSchema):
    token: str = field(default=None, description="Authentication token")
