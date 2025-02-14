import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from .base import Base
from server.resources.geometry import Vector3f, Vector4f


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
    __allow_update__ = set(['type', 'name', 'color', 'position', 'position.x', 'position.y', 'position.z',
                            'scale.x', 'scale.y', 'scale.z', 'orientation.x', 'orientation.y', 'orientation.z', 'orientation.w'])
    __tablename__ = "map_markers"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    location_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("locations.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), nullable=True)

    type: Mapped[str] = mapped_column(default="object")
    name: Mapped[str] = mapped_column(default="New Marker")
    color: Mapped[str] = mapped_column(default="#cc6677")

    position_x: Mapped[float] = mapped_column(default=0.0)
    position_y: Mapped[float] = mapped_column(default=0.0)
    position_z: Mapped[float] = mapped_column(default=0.0)

    scale_x: Mapped[float] = mapped_column(default=1.0)
    scale_y: Mapped[float] = mapped_column(default=1.0)
    scale_z: Mapped[float] = mapped_column(default=1.0)

    orientation_x: Mapped[float] = mapped_column(default=0.0)
    orientation_y: Mapped[float] = mapped_column(default=0.0)
    orientation_z: Mapped[float] = mapped_column(default=0.0)
    orientation_w: Mapped[float] = mapped_column(default=1.0)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    position: Mapped[Vector3f] = composite(position_x, position_y, position_z)
    scale: Mapped[Vector3f] = composite(scale_x, scale_y, scale_z)
    orientation: Mapped[Vector4f] = composite(orientation_x, orientation_y, orientation_z, orientation_w)
