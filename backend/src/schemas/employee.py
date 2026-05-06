"""Pydantic-схемы для представления сотрудников."""

from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from .mediafile import MediaFileRead


class EmployeeRead(BaseModel):
    """Схема сотрудника для ответов API."""

    id: UUID
    full_name: str
    position: str
    photo: MediaFileRead | None = None

    model_config = ConfigDict(from_attributes=True)


class EmployeeCreateRequest(BaseModel):
    """Схема создания сотрудника с опциональной первичной загрузкой фото."""

    full_name: str
    position: str
    experience: str
    photo_filename: str | None = None
    content_type: str | None = None

    @model_validator(mode="after")
    def validate_photo_upload_fields(self) -> Self:
        """Требует передавать метаданные фото только полной парой полей."""
        if (self.photo_filename is None) != (self.content_type is None):
            raise ValueError("photo_filename and content_type must be provided together")
        return self


class EmployeePutResponse(BaseModel):
    """Ответ на создание или обновление фото сотрудника с upload URL."""

    id: UUID
    full_name: str
    position: str
    experience: str | None
    photo: MediaFileRead | None
    presigned_url: str | None


class EmployeePatchRequest(BaseModel):
    """Схема частичного обновления базовых данных сотрудника."""

    full_name: str
    position: str
    experience: str


class EmployeePhotoUpdateRequest(BaseModel):
    """Схема запроса на перевыпуск URL для загрузки фото сотрудника."""

    photo_filename: str
    content_type: str
