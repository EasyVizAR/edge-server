import datetime
import time
import uuid

from dataclasses import field
from marshmallow_dataclass import dataclass

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from server.resources.db import Base, MigrationSchema
from server.resources.geometry import Vector3f, Vector4f


class DevicePose(Base):
    """
    Record of a mobile device's position and orientation at a point in time.
    """
    __tablename__ = "device_poses"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    tracking_session_id: Mapped[int] = mapped_column(sa.ForeignKey("tracking_sessions.id"))
    mobile_device_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("mobile_devices.id"))

    position_x: Mapped[float] = mapped_column()
    position_y: Mapped[float] = mapped_column()
    position_z: Mapped[float] = mapped_column()
    position: Mapped[Vector3f] = composite(position_x, position_y, position_z)

    orientation_x: Mapped[float] = mapped_column()
    orientation_y: Mapped[float] = mapped_column()
    orientation_z: Mapped[float] = mapped_column()
    orientation_w: Mapped[float] = mapped_column()
    orientation: Mapped[Vector4f] = composite(orientation_x, orientation_y, orientation_z, orientation_w)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)


class PoseChangeSchema(MigrationSchema):
    __convert_isotime_fields__ = ['time']

    class Meta:
        model = DevicePose
        load_instance = True

    time = auto_field('created_time', description="Time the pose was recorded")
    position = Nested(Vector3f.Schema, description="Position in world coordinates (x, y, z)", many=False)
    orientation = Nested(Vector4f.Schema, description="Orientation (quaternion)", many=False)
