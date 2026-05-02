"""Pydantic-схемы пользователей."""

import uuid

from pydantic import BaseModel

from src.models.user import UserRole


class User(BaseModel):
    """Базовая схема пользователя."""

    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    """Схема пользователя с полями, сохраняемыми в базе данных."""

    hashed_password: str


class UserResponse(BaseModel):
    """Схема пользователя для ответов API."""

    id: uuid.UUID
    username: str
    role: UserRole
    is_active: bool

    model_config = {
        "from_attributes": True,
    }
