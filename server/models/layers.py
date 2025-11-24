import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from .base import Base
from server import messages_pb2
from server.resources.geometry import Box
from server.utils import utils



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
    __allow_update__ = ['name', 'type', 'image_type', 'reference_height', 'boundary.left', 'boundary.top', 'boundary.width', 'boundary.height']

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    location_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("locations.id", ondelete="CASCADE"))

    name: Mapped[str] = mapped_column(default="New Layer")
    type: Mapped[str] = mapped_column(default="generated")
    version: Mapped[int] = mapped_column(default=0)

    image_type: Mapped[str] = mapped_column(default="image/png")

    boundary_left: Mapped[float] = mapped_column(default=0.0)
    boundary_top: Mapped[float] = mapped_column(default=0.0)
    boundary_width: Mapped[float] = mapped_column(default=0.0)
    boundary_height: Mapped[float] = mapped_column(default=0.0)

    reference_height: Mapped[float] = mapped_column(default=0.0)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    boundary: Mapped[Box] = composite(boundary_left, boundary_top, boundary_width, boundary_height)

    def to_protobuf(self):
        """
        Get protobuf message from object.
        """
        layer_type = utils.string_to_enum(self.type, "layer")

        layer = messages_pb2.Layer()
        layer.type = messages_pb2.LayerType.Value(layer_type)
        layer.name = self.name
        layer.version = self.version
        layer.image_type = self.image_type
        layer.boundary.left = self.boundary_left
        layer.boundary.top = self.boundary_top
        layer.boundary.width = self.boundary_width
        layer.boundary.height = self.boundary_height
        layer.reference_height = self.reference_height
        return layer
