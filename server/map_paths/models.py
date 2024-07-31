import datetime
import time
import uuid

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from server.models.map_paths import MapPath


class MapPathSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = MapPath
        load_instance = True

    id = auto_field(description="Path ID")

    location_id = auto_field(description="Location for which the path is valid")
    mobile_device_id = auto_field(description="(optional) specific user device that should display the path")
    target_marker_id = auto_field(description="(optional) if path is used for navigation, the target marker ID")

    type = auto_field(description="Path type (unknown|navigation|object|drawing)")
    color = auto_field(description="Suggested display color for the path as a seven-character HTML color code")
    label = auto_field(description="Path name to be displayed in the user interface")

    points = auto_field(description="List of points, each point being a list of floats (x, y, z)")

    created_time = auto_field(description="Time the path was created")
