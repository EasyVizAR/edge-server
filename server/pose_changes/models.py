import datetime
import time
import uuid

from dataclasses import field
from marshmallow_dataclass import dataclass

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from server.models.device_poses import DevicePose
from server.resources.db import MigrationSchema
from server.resources.geometry import Vector3f, Vector4f


class PoseChangeSchema(MigrationSchema):
    __convert_isotime_fields__ = ['time']

    class Meta:
        model = DevicePose
        load_instance = True

    time = auto_field('created_time', description="Time the pose was recorded")
    position = Nested(Vector3f.Schema, description="Position in world coordinates (x, y, z)", many=False)
    orientation = Nested(Vector4f.Schema, description="Orientation (quaternion)", many=False)
