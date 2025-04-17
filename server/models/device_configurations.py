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
    __allow_update__ = set(['enable_mesh_capture', 'enable_photo_capture',
        'enable_extended_capture', 'photo_capture_mode',
        'photo_detection_threshold', 'photo_target_interval',
        'enable_gesture_recognition', 'enable_marker_placement'])

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    location_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("locations.id"), nullable=True)
    mobile_device_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("mobile_devices.id"), nullable=True)

    enable_mesh_capture: Mapped[bool] = mapped_column(default=False)
    enable_photo_capture: Mapped[bool] = mapped_column(default=False) # deprecated: use photo_capture_mode instead
    enable_extended_capture: Mapped[bool] = mapped_column(default=False)

    photo_capture_mode: Mapped[str] = mapped_column(default="off")
    photo_detection_threshold: Mapped[float] = mapped_column(default=0.65)
    photo_target_interval: Mapped[str] = mapped_column(default=5)
    enable_gesture_recognition: Mapped[bool] = mapped_column(default=False)
    enable_marker_placement: Mapped[bool] = mapped_column(default=False)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    def __init__(self, *args, **kwargs):
        # It may seem redundant to set these explicitly in the constructor
        # given all of the columns have default values. However, the default
        # value is not used during object creation, so we need to do this.

        self.enable_mesh_capture = False
        self.enable_photo_capture = False
        self.enable_extended_capture = False

        self.photo_capture_mode = "off"
        self.photo_detection_threshold = 0.65
        self.photo_target_interval = 5
        self.enable_gesture_recognition = False
        self.enable_marker_placement = False

        super(DeviceConfiguration, self).__init__(*args, **kwargs)
