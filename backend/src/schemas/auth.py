"""Pydantic-схемы для запросов и ответов аутентификации."""

from pydantic import BaseModel, Field

from src.models.user import UserRole
from src.schemas.token import TokenResponse
from src.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Тело запроса на вход пользователя."""

    username: str
    password: str


class LoginResponse(TokenResponse):
    """Ответ на успешный вход пользователя."""

    user: UserResponse


class RegisterRequest(BaseModel):
    """Тело запроса на регистрацию пользователя."""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    role: UserRole = UserRole.EMPLOYEE
