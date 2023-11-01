import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column

from .base import Base


class User(Base):
    """
    A user.
    """
    __allow_update__ = set(['display_name'])
    __tablename__ = "users"
    __table_args__ = (
        sa.UniqueConstraint("name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column()
    password: Mapped[str] = mapped_column()
    display_name: Mapped[str] = mapped_column()
    type: Mapped[str] = mapped_column()

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
