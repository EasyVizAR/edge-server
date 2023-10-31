import datetime
import time
import uuid

from marshmallow import post_dump
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from server.headset.models import MobileDevice
from server.resources.db import Base


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

    location_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("locations.id"))
    mobile_device_id: Mapped[int] = mapped_column(sa.ForeignKey("mobile_devices.id"), nullable=True)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)


class SurfaceSchema(SQLAlchemySchema):
    class Meta:
        model = Surface
        load_instance = True

    id = auto_field(description="Surface ID (UUID)")

    uploadedBy = auto_field('mobile_device_id', description="Device ID that uploaded the surface")

    created = auto_field('created_time', description="Time the surface was created")
    updated = auto_field('updated_time', description="Time the surface was last updated")

    @post_dump(pass_original=True)
    def add_file_url(self, data, original, **kwargs):
        """
        Add the fileUrl expected by certain clients.
        """
        data['fileUrl'] = '/locations/{}/surfaces/{}/surface.ply'.format(original.location_id, original.id)
        return data
