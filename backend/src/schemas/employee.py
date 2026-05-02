"""Pydantic-схемы для представления сотрудников."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .mediafile import MediaFileRead


class EmployeeRead(BaseModel):
    """Схема сотрудника для ответов API."""

    id: UUID
    full_name: str
    position: str
    photo: MediaFileRead | None = None

    model_config = ConfigDict(from_attributes=True)
