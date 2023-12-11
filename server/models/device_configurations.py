import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from .base import Base


class DeviceConfiguration(Base):
    """
    A set of configuration values for a single device or for all devices in a
    given location.
    """
    __tablename__ = "device_configurations"
    __allow_update__ = set(['enable_mesh_capture', 'enable_photo_capture', 'enable_extended_capture'])

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    location_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("locations.id"), nullable=True)
    mobile_device_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("mobile_devices.id"), nullable=True)

    enable_mesh_capture: Mapped[bool] = mapped_column(default=True)
    enable_photo_capture: Mapped[bool] = mapped_column(default=False)
    enable_extended_capture: Mapped[bool] = mapped_column(default=False)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
