import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from .base import Base
from server.resources.geometry import Vector3f, Vector4f


class DevicePose(Base):
    """
    Record of a mobile device's position and orientation at a point in time.
    """
    __tablename__ = "device_poses"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    tracking_session_id: Mapped[int] = mapped_column(sa.ForeignKey("tracking_sessions.id", ondelete="CASCADE"))
    mobile_device_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("mobile_devices.id", ondelete="CASCADE"))

    position_x: Mapped[float] = mapped_column()
    position_y: Mapped[float] = mapped_column()
    position_z: Mapped[float] = mapped_column()

    orientation_x: Mapped[float] = mapped_column()
    orientation_y: Mapped[float] = mapped_column()
    orientation_z: Mapped[float] = mapped_column()
    orientation_w: Mapped[float] = mapped_column()

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    position: Mapped[Vector3f] = composite(position_x, position_y, position_z)
    orientation: Mapped[Vector4f] = composite(orientation_x, orientation_y, orientation_z, orientation_w)
