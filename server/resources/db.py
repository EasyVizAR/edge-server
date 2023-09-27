import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from marshmallow import post_dump
from marshmallow_sqlalchemy import SQLAlchemySchema


class Base(orm.DeclarativeBase):
    pass


class MigrationSchema(SQLAlchemySchema):
    __convert_isotime_fields__ = []

    @post_dump
    def convert_isotime(self, data, **kwargs):
        """
        Convert designated fields from ISO string to Unix timestamp.

        This will convert any fields listed in __convert_isotime_fields__.
        This is intended for compatibility for older API functions that
        returned float times and should not be used in the v2 API.
        """
        for field in self.__convert_isotime_fields__:
            iso = data.get(field)
            if iso is None:
                continue
            dt = datetime.datetime.fromisoformat(iso)
            data[field] = dt.timestamp()
        return data
