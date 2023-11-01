import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from .base import Base



class Incident(Base):
    """
    An incident represents an world event with a definite start time.

    It also serves as a container for data created during that event
    such as device location history, photos, and 3D geometry.
    """
    __tablename__ = "incidents"
    __allow_update__ = ['name']

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(default="New Incident")

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
