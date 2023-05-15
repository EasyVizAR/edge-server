import time

from dataclasses import field
from marshmallow_dataclass import dataclass

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, composite, mapped_column

from server.resources.csvresource import CsvResource
from server.resources.db import Base
from server.resources.geometry import Vector3f, Vector4f


@dataclass
class PoseChangeModel(CsvResource):
    """
    Record of a headset's position and orientation at a point in time.

    Deprecated: new code should use PoseChange instead.  Alembic migration code
    may still use PoseChangeModel until storage migration is stabilized.
    """
    time:           float = field(default_factory=time.time)
    position:       Vector3f = field(default_factory=Vector3f)
    orientation:    Vector4f = field(default_factory=Vector4f)


class PoseChange(Base):
    __tablename__ = "pose_changes"

    id: Mapped[int] = mapped_column(primary_key=True)

    incident_id: Mapped[str] = mapped_column()
    headset_id: Mapped[str] = mapped_column()
    check_in_id: Mapped[int] = mapped_column(nullable=True)

    time: Mapped[float] = mapped_column(default=time.time)

    position_x: Mapped[float] = mapped_column()
    position_y: Mapped[float] = mapped_column()
    position_z: Mapped[float] = mapped_column()
    position: Mapped[Vector3f] = composite(position_x, position_y, position_z)

    orientation_x: Mapped[float] = mapped_column()
    orientation_y: Mapped[float] = mapped_column()
    orientation_z: Mapped[float] = mapped_column()
    orientation_w: Mapped[float] = mapped_column()
    orientation: Mapped[Vector4f] = composite(orientation_x, orientation_y, orientation_z, orientation_w)


class PoseChangeSchema(SQLAlchemySchema):
    class Meta:
        model = PoseChange
        load_instance = True

    time = auto_field()
    position = Nested(Vector3f.Schema, many=False)
    orientation = Nested(Vector4f.Schema, many=False)
