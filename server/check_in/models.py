import datetime
import time
import uuid

from marshmallow_sqlalchemy import auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from server.resources.db import Base, MigrationSchema

from server.location.models import Location


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
    mobile_device_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("mobile_devices.id"))

    incident_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("incidents.id"))
    location_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("locations.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(nullable=True)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)


class CheckInSchema(MigrationSchema):
    __convert_isotime_fields__ = ['start_time']

    class Meta:
        model = TrackingSession
        load_instance = True

    id = auto_field(description="Tracking session ID")

    location_id = auto_field()

    start_time = auto_field('created_time',
        description="Session starting time when the device initially checked in",
        dump_only=True)
