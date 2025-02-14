import datetime
import time
import uuid

from marshmallow import post_dump
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from server.models.device_configurations import DeviceConfiguration
from server.models.locations import Location
from server.resources.db import MigrationSchema


class DeviceConfigurationSchema(SQLAlchemySchema):
    class Meta:
        model = DeviceConfiguration
        load_instance = True

    enable_mesh_capture = auto_field(description="Enable automatic capturing of environment surfaces for mapping")
    enable_photo_capture = auto_field(description="Enable automatic capturing of high resolution photos (deprecated)")
    enable_extended_capture = auto_field(description="Enable automatic capturing of photos, depth, geometry, and intensity images")

    photo_capture_mode = auto_field(description="Automatic photo capture mode (off|objects|people|continuous)")
    photo_detection_threshold = auto_field(description="Score threshold applied during object detection (range 0-1, default: 0.65)")
    photo_target_interval = auto_field(description="Desired photo upload interval used by some modes (seconds, default: 5)")
    enable_gesture_recognition = auto_field(description="Enable experimental gesture controls")
    enable_marker_placement = auto_field(description="Enable marker placement")


class LocationSchema(MigrationSchema):
    __convert_isotime_fields__ = ['created_time', 'updated_time']

    class Meta:
        model = Location
        load_instance = True

    id = auto_field(description="Location ID (UUID)")

    name = auto_field(description="Location name")
    description = auto_field(description="Location description")

    model_version = auto_field(description="Model version, incremented whenever the location 3D model is updated")

    created_time = auto_field(description="Time the location was created")
    updated_time = auto_field(description="Last time the location was updated")

    #device_configuration = Nested(DeviceConfigurationSchema, many=False)

    @post_dump(pass_original=True)
    def add_headset_configuration(self, data, original, **kwargs):
        if original.has('device_configuration'):
            schema = DeviceConfigurationSchema()
            data['headset_configuration'] = schema.dump(original.device_configuration)
        return data
