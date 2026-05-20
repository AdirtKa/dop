from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.media_file import MediaFile
    from src.models.user import User


class EventHall(StrEnum):
    small = "small"
    buffet = "buffet"
    large = "large"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False, default="")
    representative: Mapped[str] = mapped_column(Text, nullable=False, default="")
    responsible_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    responsible_contact: Mapped[str] = mapped_column(Text, nullable=False, default="")
    halls: Mapped[list[EventHall]] = mapped_column(
        ARRAY(Enum(EventHall, name="event_hall")),
        nullable=False,
        default=lambda: [EventHall.large],
    )

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    organization: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[organization_id],
    )

    media: Mapped[list["MediaFile"]] = relationship(
        secondary="event_media",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
