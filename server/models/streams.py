import datetime
import secrets
import uuid

from typing import List

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from .base import Base


def generate_token():
    return secrets.token_urlsafe(16)


class Stream(Base):
    """
    A video stream.
    """
    __tablename__ = "streams"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    token: Mapped[str] = mapped_column(default=generate_token)
    description: Mapped[str] = mapped_column(default="Stream")

    publisher_addr: Mapped[str] = mapped_column(default=None, nullable=True)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
