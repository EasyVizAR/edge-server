import datetime
import time
import uuid

from marshmallow import post_dump
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from server.models.layers import Layer
from server.resources.geometry import Box


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
