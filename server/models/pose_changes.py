import datetime
import time
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from .base import Base
from server.resources.geometry import Vector3f, Vector4f


class PoseChange(Base):
    """
    Record of a mobile device's position and orientation at a point in time.

    Deprecated: we are now using device_poses instead. However, some entries
    may still exist in the pose_changes table if they were not migrated.
    """
    __tablename__ = "pose_changes"

    id: Mapped[int] = mapped_column(primary_key=True)

    incident_id: Mapped[str] = mapped_column()
    headset_id: Mapped[str] = mapped_column()
    check_in_id: Mapped[int] = mapped_column(nullable=True)

    time: Mapped[float] = mapped_column(default=time.time)

    position_x: Mapped[float] = mapped_column()
    position_y: Mapped[float] = mapped_column()
    position_z: Mapped[float] = mapped_column()
    position: Mapped[Vector3f] = composite(position_x, position_y, position_z)

    orientation_x: Mapped[float] = mapped_column()
    orientation_y: Mapped[float] = mapped_column()
    orientation_z: Mapped[float] = mapped_column()
    orientation_w: Mapped[float] = mapped_column()
    orientation: Mapped[Vector4f] = composite(orientation_x, orientation_y, orientation_z, orientation_w)
