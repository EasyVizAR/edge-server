import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from .base import Base


class TrackingSession(Base):
    """
    Record of a mobile device tracking session. This is the first time the
    mobile device scans a QR code and makes its presence at a location known to
    us.

    Devices can begin a tracking session in various ways. Tracking sessions can
    be explicitly created by a POST request, but they are also automatically
    created when a device changes its location_id through a PUT or PATCH
    operation or even when the device first registers.
    """
    __tablename__ = "tracking_sessions"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    mobile_device_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("mobile_devices.id", ondelete="CASCADE"))
    incident_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("incidents.id", ondelete="CASCADE"))
    location_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("locations.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), nullable=True)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
