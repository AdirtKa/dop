"""Pydantic-схемы для JWT-токенов."""

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Ответ с выпущенным access-token."""

    access_token: str
    token_type: str = "bearer"  # noqa S105


class TokenData(BaseModel):
    """Данные токена, используемые внутри приложения."""

    username: str | None = None
