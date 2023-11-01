import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from .base import Base



class DetectionTask(Base):
    __tablename__ = "detection_tasks"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    photo_record_id: Mapped[int] = mapped_column(sa.ForeignKey("photo_records.id", ondelete="CASCADE"))

    model_family: Mapped[str] = mapped_column(default="")
    model_name: Mapped[str] = mapped_column(default="")
    engine_name: Mapped[str] = mapped_column(default="")
    engine_version: Mapped[str] = mapped_column(default="")
    cuda_enabled: Mapped[bool] = mapped_column(default=False)

    preprocess_duration: Mapped[float] = mapped_column(default=0.0)
    execution_duration: Mapped[float] = mapped_column(default=0.0)
    postprocess_duration: Mapped[float] = mapped_column(default=0.0)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
