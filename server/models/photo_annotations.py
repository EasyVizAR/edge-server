import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from .base import Base
from server.resources.geometry import Box


class PhotoAnnotation(Base):
    __tablename__ = "photo_annotations"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    photo_record_id: Mapped[int] = mapped_column(sa.ForeignKey("photo_records.id", ondelete="CASCADE"))
    detection_task_id: Mapped[int] = mapped_column(sa.ForeignKey("detection_tasks.id", ondelete="CASCADE"))

    label: Mapped[str] = mapped_column(default="unknown")
    confidence: Mapped[float] = mapped_column(default=0.0)

    boundary_left: Mapped[float] = mapped_column(default=0.0)
    boundary_top: Mapped[float] = mapped_column(default=0.0)
    boundary_width: Mapped[float] = mapped_column(default=0.0)
    boundary_height: Mapped[float] = mapped_column(default=0.0)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    boundary: Mapped[Box] = composite(boundary_left, boundary_top, boundary_width, boundary_height)
