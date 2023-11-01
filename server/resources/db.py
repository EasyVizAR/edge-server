import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from marshmallow import pre_load, post_dump
from marshmallow_sqlalchemy import SQLAlchemySchema

from server.utils.patch import patch_object


class MigrationSchema(SQLAlchemySchema):
    __convert_isotime_fields__ = []

    @pre_load
    def convert_timestamp(self, data, **kwargs):
        """
        Convert designated fields from timestamp to ISO string.
        """
        for field in self.__convert_isotime_fields__:
            ts = data.get(field)
            if ts is not None:
                dt = datetime.datetime.fromtimestamp(ts)
                data[field] = dt.isoformat()
        return data

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
            if iso is not None:
                dt = datetime.datetime.fromisoformat(iso)
                data[field] = dt.timestamp()
        return data
