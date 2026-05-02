"""Pydantic-схемы для представления медиафайлов."""

from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class MediaFileRead(BaseModel):
    """Схема медиафайла для ответов API."""

    id: UUID
    public_url: str | None
    mime_type: str
    kind: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
