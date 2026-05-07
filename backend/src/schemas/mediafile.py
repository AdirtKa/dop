"""Pydantic-схемы для представления медиафайлов."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MediaFileRead(BaseModel):
    """Схема медиафайла для ответов API."""

    id: UUID
    public_url: str | None
    mime_type: str
    kind: str
    status: str | None = "ready"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
