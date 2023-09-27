import datetime
import time
import uuid

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from server.resources.dataclasses import dataclass, field
from server.resources.db import Base, MigrationSchema
from server.resources.jsonresource import JsonResource
from server.resources.geometry import Vector3f


# DEPRECATED
@dataclass
class FeatureDisplayStyle:
    placement:  str = field(default="point")
    leftOffset: float = field(default=None)
    topOffset:  float = field(default=None)
    radius:     float = field(default=None)


# DEPRECATED
@dataclass
class FeatureModel(JsonResource):
    """
    A map feature such as an important object or location.

    A feature should have a descriptive name, a position in world coordinates,
    and a type, which affects how it is displayed in AR and map overlays.

    Some supported feature types are: fire, warning, injury, door, elevator,
    stairs, user, object, extinguisher, message, headset, ambulance.

    The style field contains additional information for rendering, especially
    in the AR view.

    Placement types:
        "point" - a marker placed at a fixed location
        "floating" - the icon or text should remain in view at a fixed position
                     which is relative to the top-left corner of the AR display
        "surface" - the marker should be rendered on a physical surface such as
                    a wall, at a fixed position relative to the top-left corner
                    of the surface

    Feature types:
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
    id: int

    name:           str = field(default="New Feature",
                                description="Name for the feature")
    color:          str = field(default="#cc6677",
                                description="Suggested display color for the feature as a seven-character HTML color code.")
    position:       Vector3f = field(default_factory=Vector3f,
                                description="Position in world coordinates")
    type:           str = field(default="object",
                                description="Feature type (ambulance|door|elevator|extinguisher|fire|headset|injury|message|object|photo|point|stairs|user|warning)")
    style:          FeatureDisplayStyle = field(default_factory=FeatureDisplayStyle,
                                description="Style information for rendering the feature in AR")

    createdBy:      str = field(default=None,
                                description="User or headset that created the feature")

    created:        float = field(default_factory=time.time)
    updated:        float = field(default_factory=time.time)


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
