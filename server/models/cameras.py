import datetime
import secrets
import uuid

from typing import List

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from .base import Base
from .device_configurations import DeviceConfiguration


class Camera(Base):
    valid_types = set(["unknown", "color", "thermal"])

    """
    Camera information.

    Generally, every mobile device is assumed to have a camera.  In cases where
    there are multiple cameras (e.g. headset user carrying a thermal camera),
    then we create a second mobile device as a child of the headset with its
    own position history and camera parameters.
    """
    __allow_update__ = set(['type', 'width', 'height', 'fx', 'fy', 'cx', 'cy',
        'k1', 'k2', 'p1', 'p2'])
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    mobile_device_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("mobile_devices.id", ondelete="CASCADE"))

    type: Mapped[str] = mapped_column(default="color")

    # Camera calibration parameters
    width: Mapped[int] = mapped_column(default=0)
    height: Mapped[int] = mapped_column(default=0)
    fx: Mapped[float] = mapped_column(default=0.0)
    fy: Mapped[float] = mapped_column(default=0.0)
    cx: Mapped[float] = mapped_column(default=0.0)
    cy: Mapped[float] = mapped_column(default=0.0)
    k1: Mapped[float] = mapped_column(default=0.0)
    k2: Mapped[float] = mapped_column(default=0.0)
    p1: Mapped[float] = mapped_column(default=0.0)
    p2: Mapped[float] = mapped_column(default=0.0)

    def get_relative_focal_lengths(self):
        """
        Return relative focal lengths as tuple (fx, fy).
        """
        return (self.fx / self.width, self.fy / self.height)
