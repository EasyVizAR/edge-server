import datetime
import time
import uuid

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from server.models.incidents import Incident
from server.resources.db import MigrationSchema


class IncidentSchema(MigrationSchema):
    __convert_isotime_fields__ = ['created', 'updated']

    class Meta:
        model = Incident
        load_instance = True

    id = auto_field(description="Incident ID (UUID)")
    name = auto_field(description="Incident name")

    created = auto_field('created_time', description="Time the incident was created")
    updated = auto_field('updated_time', description="Time the incident was last updated")
