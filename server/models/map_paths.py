import datetime
import uuid

from typing import List

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from .base import Base
from server.resources.geometry import Vector3f


class MapPath(Base):
    """
    A map path is a sequence of points that can be visualized as connected line segments on the map.

    Map paths may indicate navigation directions to a waypoint, object
    contours, or visible drawings on walls or floors.  They may be calculated
    from a navigation mesh or drawn by hand.

    Paths which are for navigation may specify a specific user device ID, in which case,
    in which case they should only be displayed on that device. Otherwise, they may be
    visible to everyone. The path may specify some hints for the visual appearance of the
    line including a text label and color. This may be useful for displaying different
    trails, e.g. a path to the fire in red and a path to a victim in blue.
    """
    __tablename__ = "map_paths"
    __allow_update__ = set(['mobile_device_id', 'target_marker_id', 'type', 'color', 'label', 'points'])

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    location_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("locations.id", ondelete="CASCADE"))
    mobile_device_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, sa.ForeignKey("mobile_devices.id", ondelete="UPDATE"), nullable=True)
    target_marker_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("map_markers.id", ondelete="UPDATE"), nullable=True)

    type: Mapped[str] = mapped_column(default="unknown")
    color: Mapped[str] = mapped_column(default="#00ff00")
    label: Mapped[str] = mapped_column(default="Path")

    points: Mapped[List[List[float]]] = mapped_column(sa.JSON, default=list)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
