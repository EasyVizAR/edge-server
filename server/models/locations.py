import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from .base import Base
from .device_configurations import DeviceConfiguration
from .photo_records import PhotoRecord


class Location(Base):
    """
    A location such as a building with a definite geographical boundary.

    A location may have one or more map markers, which are points of interest,
    messages, or other pieces digital information that team members would like
    to share.

    A location may have one or more map layers, e.g. a floor plan for each
    floor of a building.
    """
    __tablename__ = "locations"
    __allow_update__ = set(['name', 'description'])

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    last_color_source_id: Mapped[int] = mapped_column(sa.ForeignKey("photo_records.id", ondelete="SET NULL", onupdate="CASCADE"))

    name: Mapped[str] = mapped_column(default="New Location")
    description: Mapped[str] = mapped_column(default="")

    model_version: Mapped[int] = mapped_column(default=0)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    device_configuration: Mapped[DeviceConfiguration] = relationship(cascade="all, delete-orphan", uselist=False)
    last_color_source: Mapped[PhotoRecord] = relationship(foreign_keys=[last_color_source_id])
