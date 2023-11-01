import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from .base import Base


class PhotoQueue(Base):
    __tablename__ = "photo_queues"

    name: Mapped[str] = mapped_column(primary_key=True)

    next_queue_name: Mapped[str] = mapped_column(sa.ForeignKey("photo_queues.name"), default="done", nullable=True)

    display_order: Mapped[int] = mapped_column(default=0)
    description: Mapped[str] = mapped_column(default="")
