"""ORM-модель сотрудника."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


if TYPE_CHECKING:
    from src.models.media_file import MediaFile


class Employee(Base):
    """ORM-модель сотрудника, отображаемого в каталоге."""

    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    full_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    position: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    experience: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    photo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("media_files.id", ondelete="SET NULL"),
        nullable=True,
    )

    photo: Mapped["MediaFile | None"] = relationship(
        "MediaFile",
        back_populates="employees",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
