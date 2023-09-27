import datetime
import time
import uuid

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from dataclasses import field
from marshmallow_dataclass import dataclass

from server.check_in.models import CheckInModel
from server.location.models import LocationModel
from server.photo.models import PhotoModel

from server.resources.db import Base
from server.resources.dictresource import DictResource, DictCollection
from server.resources.jsonresource import JsonResource, JsonCollection


@dataclass
class HeadsetContainer(DictResource):
    id: str = field(default=None)

    def on_ready(self):
        self.CheckIn = JsonCollection(CheckInModel, "check-in", parent=self)


@dataclass
class IncidentModel(JsonResource):
    """
    An incident represents an world event with a definite start time.

    It also serves as a container for data created during that event
    such as headset location history, photos, and 3D geometry.
    """
    id:         str = field(default=None)
    name:       str = field(default=None)
    created:    float = field(default_factory=time.time)

    def on_ready(self):
        self.Headset = DictCollection(HeadsetContainer, "headsets", id_type="uuid", parent=self)
        self.Location = JsonCollection(LocationModel, "location", id_type="uuid", parent=self)
        self.Photo = JsonCollection(PhotoModel, "photo", id_type="uuid", parent=self)


IncidentLoader = JsonCollection(IncidentModel, "incident", id_type="uuid")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(default="New Incident")

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)


class IncidentSchema(SQLAlchemySchema):
    class Meta:
        model = Incident
        load_instance = True

    id = auto_field()
    name = auto_field()
    created = auto_field('created_time', dump_only=True)
