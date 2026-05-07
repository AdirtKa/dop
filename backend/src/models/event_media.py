from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import Base

event_media = Table(
    "event_media",
    Base.metadata,
    Column(
        "event_id",
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "media_file_id",
        UUID(as_uuid=True),
        ForeignKey("media_files.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
