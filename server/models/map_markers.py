import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from .base import Base
from server.resources.geometry import Vector3f


class MapMarker(Base):
    """
    A map marker such as an important object or location.

    A marker should have a descriptive name, a position in world coordinates,
    and a type, which affects what is displayed in AR and map overlays.

    Supported marker types:
        ambulance
        audio
        bad-person
        biohazard
        door
        elevator
        exit
        extinguisher
        fire
        headset
        injury
        message
        object
        person
        photo
        point
        radiation
        stairs
        user
        warning
    """
    __tablename__ = "map_markers"
    __allow_update__ = ['type', 'name', 'color', 'position_x', 'position_y', 'position_z', 'position']

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    location_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("locations.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), nullable=True)

    type: Mapped[str] = mapped_column(default="object")
    name: Mapped[str] = mapped_column(default="New Marker")
    color: Mapped[str] = mapped_column(default="#cc6677")

    position_x: Mapped[float] = mapped_column(default=0.0)
    position_y: Mapped[float] = mapped_column(default=0.0)
    position_z: Mapped[float] = mapped_column(default=0.0)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    position: Mapped[Vector3f] = composite(position_x, position_y, position_z)
