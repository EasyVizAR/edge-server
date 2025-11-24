import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from .base import Base
from server import messages_pb2
from server.resources.geometry import Box, Vector3f, Vector4f
from server.utils import utils


class Surface(Base):
    """
    A surface is a triangle mesh that can be tracked by a persistent UUID.

    Surfaces are uploaded and stored as PLY files and used by the mapping
    module to produce approximate floor plans for a location.

    Below is an example PLY file which contains a triangle mesh consisting of a
    single triangle.

        ply
        format ascii 1.0
        comment Surface ID: {7696b5c8-272c-46b3-8b9c-98befaa6a9f1}
        element vertex 3
        property double x
        property double y
        property double z
        property double nx
        property double ny
        property double nz
        element face 1
        property list uchar int vertex_index
        end_header
        0.445517 -1.057148 -1.517160 0.000000 0.000000 0.000000
        0.476931 -1.052150 -1.492400 0.000000 0.000000 0.000000
        0.438819 -1.044527 -1.573302 0.000000 0.000000 0.000000
        3 0 1 2
    """
    __tablename__ = "surfaces"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    location_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("locations.id", ondelete="CASCADE"))
    mobile_device_id: Mapped[int] = mapped_column(sa.ForeignKey("mobile_devices.id"), nullable=True)

    version: Mapped[int] = mapped_column(default=0)
    num_faces: Mapped[int] = mapped_column(default=0)
    num_vertices: Mapped[int] = mapped_column(default=0)

    boundary_left: Mapped[float] = mapped_column(default=0.0)
    boundary_top: Mapped[float] = mapped_column(default=0.0)
    boundary_width: Mapped[float] = mapped_column(default=0.0)
    boundary_height: Mapped[float] = mapped_column(default=0.0)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    boundary: Mapped[Box] = composite(boundary_left, boundary_top, boundary_width, boundary_height)

    def to_protobuf(self):
        """
        Get protobuf message from object.
        """
        surface_type = utils.string_to_enum("default", "surface")

        surface = messages_pb2.Surface()
        surface.type = messages_pb2.SurfaceType.Value(surface_type)
        surface.version = self.version
        surface.num_faces = self.num_faces
        surface.num_vertices = self.num_vertices
        surface.boundary.left = self.boundary_left
        surface.boundary.top = self.boundary_top
        surface.boundary.width = self.boundary_width
        surface.boundary.height = self.boundary_height
        return surface
