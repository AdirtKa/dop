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


class EmployeeCreate(BaseModel):
    """Схема создания сотрудника для получения в API."""

    full_name: str
    position: str
    experience: str
    photo_filename: str
    content_type: str


class EmployeeUpdateResponse(BaseModel):
    id: UUID
    full_name: str
    position: str
    experience: str
    photo: MediaFileRead | None = None
    presigned_url: str
