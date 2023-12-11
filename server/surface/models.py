import datetime
import time
import uuid

from marshmallow import post_dump
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from server.headset.models import MobileDevice
from server.models.surfaces import Surface


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
