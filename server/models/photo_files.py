import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from .base import Base
from .photo_records import PhotoRecord


class PhotoFile(Base):
    __tablename__ = "photo_files"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    photo_record_id: Mapped[int] = mapped_column(sa.ForeignKey("photo_records.id", ondelete="CASCADE"))

    name: Mapped[str] = mapped_column()
    purpose: Mapped[str] = mapped_column(default="photo")
    content_type: Mapped[str] = mapped_column(default="image/png")
    height: Mapped[int] = mapped_column(default=0)
    width: Mapped[int] = mapped_column(default=0)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    record: Mapped[PhotoRecord] = relationship()
