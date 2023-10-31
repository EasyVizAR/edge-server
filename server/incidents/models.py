import datetime
import time
import uuid

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from server.resources.db import Base, MigrationSchema


class Incident(Base):
    """
    An incident represents an world event with a definite start time.

    It also serves as a container for data created during that event
    such as device location history, photos, and 3D geometry.
    """
    __tablename__ = "incidents"
    __allow_update__ = ['name']

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(default="New Incident")

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)


class IncidentSchema(MigrationSchema):
    __convert_isotime_fields__ = ['created', 'updated']

    class Meta:
        model = Incident
        load_instance = True

    id = auto_field(description="Incident ID (UUID)")
    name = auto_field(description="Incident name")

    created = auto_field('created_time', description="Time the incident was created")
    updated = auto_field('updated_time', description="Time the incident was last updated")
