import datetime
import time
import uuid

from marshmallow import post_dump
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from server.resources.dataclasses import dataclass, field
from server.resources.db import Base
from server.resources.jsonresource import JsonResource
from server.resources.geometry import Box


# DEPRECATED
@dataclass
class LayerModel(JsonResource):
    """
    Graphical representation of a location, generally as a 2D map

    We support three types of layer objects, specificed in the type field.
    generated: a floor plan will be constructed automatically from surface data
    uploaded: an uploaded image
    external: a link to an external image

    For uploaded files, JPEG, PNG, and SVG are supported. We may need to add
    support for PDF uploads and probably convert to an image.

    For external files, we may want to download and store locally at some
    point.  Otherwise, these will not work in the absence of a wide area
    connection.
    """
    id: int

    name:           str = field(default="New Layer")
    type:           str = field(default="generated")
    ready:          bool = field(default=False)
    version:        int = field(default=0,
                                description="Counter that indicates the current image version.")

    contentType:    str = field(default="image/jpeg")
    imagePath:      str = field(default=None)
    imageUrl:       str = field(default=None)
    viewBox:        Box = field(default_factory=Box)

    cutting_height: float = field(default=0.0,
                                  description="Height of cutting plane for floor plan construction.")

    created:        float = field(default_factory=time.time)
    updated:        float = field(default_factory=time.time)


class Layer(Base):
    """
    Graphical representation of a location, generally as a 2D map.

    We support two types of layer objects, specified in the type field.

        generated: a floor plan constructed automatically from surface data
        uploaded: an uploaded image

    For uploaded files, JPEG, PNG, and SVG are supported. We may need to add
    support for PDF uploads and probably convert to an image.
    """
    __tablename__ = "layers"
    __allow_update__ = ['name', 'type', 'image_type', 'reference_height']

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    location_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("locations.id"))

    name: Mapped[str] = mapped_column(default="New Layer")
    type: Mapped[str] = mapped_column(default="generated")
    version: Mapped[int] = mapped_column(default=0)

    image_type: Mapped[str] = mapped_column(default="image/png")

    boundary_left: Mapped[float] = mapped_column(default=0.0)
    boundary_top: Mapped[float] = mapped_column(default=0.0)
    boundary_width: Mapped[float] = mapped_column(default=0.0)
    boundary_height: Mapped[float] = mapped_column(default=0.0)
    boundary: Mapped[Box] = composite(boundary_left, boundary_top, boundary_width, boundary_height)

    reference_height: Mapped[float] = mapped_column(default=0.0)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)


class LayerSchema(SQLAlchemySchema):
    class Meta:
        model = Layer
        load_instance = True

    id = auto_field(description="Layer ID (integer)")

    name = auto_field(description="Layer name")
    type = auto_field(description="Layer type (generated|uploaded)")
    version = auto_field(description="Layer version, incremented whenever the image changes")

    contentType = auto_field('image_type', description="Image content type")

    cutting_height = auto_field('reference_height', description="Height (Y-value) used for vertical boundary detection")

    created = auto_field('created_time', description="Time the layer was created")
    updated = auto_field('updated_time', description="Time the layer was last updated")

    @post_dump(pass_original=True)
    def add_extra_fields(self, data, original, **kwargs):
        """
        Add the imageUrl and other fields expected by certain clients.
        """
        data['imageUrl'] = '/locations/{}/layers/{}/image'.format(original.location_id, original.id)
        data['ready'] = True
        data['viewBox'] = original.boundary
        return data
