import datetime
import time
import uuid

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from server.models.map_markers import MapMarker
from server.resources.db import MigrationSchema
from server.resources.geometry import Vector3f, Vector4f


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
    scale = Nested(Vector3f.Schema, description="Feature scale (only used by volumetric features)", many=False)
    orientation = Nested(Vector4f.Schema, description="Feature orientation (quaternion, only used by certain feature types)", many=False)

    created = auto_field('created_time', description="Time the marker was created")
    updated = auto_field('updated_time', description="Time the marker was last updated")
