"""ORM-модели медиафайлов и их типов."""

from datetime import datetime
import enum
import uuid

from sqlalchemy import DateTime, Enum, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MediaKind(enum.StrEnum):
    """Перечисление типов медиафайлов."""

    image = "image"
    video = "video"


class MediaStatus(enum.StrEnum):
    pending = "pending"
    ready = "ready"
    failed = "failed"


class MediaFile(Base):
    """ORM-модель файла, хранящегося во внешнем файловом хранилище."""

    __tablename__ = "media_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    storage_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    public_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    mime_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    kind: Mapped[MediaKind] = mapped_column(
        Enum(MediaKind, name="media_kind"),
        nullable=False,
    )

    status: Mapped[MediaStatus] = mapped_column(
        Enum(MediaStatus, name="media_status"),
        nullable=False,
        default=MediaStatus.ready,
        server_default=MediaStatus.ready.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
