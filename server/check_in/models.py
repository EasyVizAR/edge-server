import datetime
import time
import uuid

from marshmallow_sqlalchemy import auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from server.models.tracking_sessions import TrackingSession
from server.resources.db import MigrationSchema

from server.location.models import Location


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
