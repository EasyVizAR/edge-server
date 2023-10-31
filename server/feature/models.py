import datetime
import time
import uuid

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from server.resources.db import Base, MigrationSchema
from server.resources.geometry import Vector3f


class MapMarker(Base):
    """
    A map marker such as an important object or location.

    A marker should have a descriptive name, a position in world coordinates,
    and a type, which affects what is displayed in AR and map overlays.

    Supported marker types:
        ambulance
        audio
        bad-person
        biohazard
        door
        elevator
        exit
        extinguisher
        fire
        headset
        injury
        message
        object
        person
        photo
        point
        radiation
        stairs
        user
        warning
    """
    __tablename__ = "map_markers"
    __allow_update__ = ['type', 'name', 'color', 'position_x', 'position_y', 'position_z', 'position']

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    location_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("locations.id"))

    user_id: Mapped[uuid.UUID] = mapped_column(nullable=True)

    type: Mapped[str] = mapped_column(default="object")
    name: Mapped[str] = mapped_column(default="New Marker")
    color: Mapped[str] = mapped_column(default="#cc6677")

    position_x: Mapped[float] = mapped_column(default=0.0)
    position_y: Mapped[float] = mapped_column(default=0.0)
    position_z: Mapped[float] = mapped_column(default=0.0)
    position: Mapped[Vector3f] = composite(position_x, position_y, position_z)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)


class FeatureSchema(MigrationSchema):
    __convert_isotime_fields__ = ['created', 'updated']

    class Meta:
        model = MapMarker
        load_instance = True

    id = auto_field(description="Marker ID")

    name = auto_field(description="Marker name, often displayed next to the marker icon")
    color = auto_field(description="Suggested display color for the marker as a seven-character HTML color code")
    type = auto_field(description="Marker type, should be one of the supported types or it may display incorrectly")

    position = Nested(Vector3f.Schema, description="Position in world coordinates", many=False)

    created = auto_field('created_time', description="Time the marker was created")
    updated = auto_field('updated_time', description="Time the marker was last updated")
