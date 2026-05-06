"""HTTP-маршруты аутентификации."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.models import User
from src.routes.auth.dependency import get_current_user
from src.schemas.auth import LoginRequest, LoginResponse
from src.schemas.token import TokenResponse
from src.schemas.user import UserResponse
from src.services.auth import login_user, logout_user, refresh_tokens
from src.session import get_session

router = APIRouter()
session_dependency = Annotated[AsyncSession, Depends(get_session)]


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    session: session_dependency,
):
    """Обрабатывает вход пользователя по логину и паролю."""
    return await login_user(
        session=session,
        request=request,
        response=response,
        username=data.username,
        password=data.password,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    session: session_dependency,
):
    """Обновляет access-token и выполняет ротацию refresh-token."""
    return await refresh_tokens(
        session=session,
        request=request,
        response=response,
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    session: session_dependency,
):
    """Завершает текущую refresh-сессию пользователя."""
    return await logout_user(
        session=session,
        request=request,
        response=response,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Возвращает профиль текущего аутентифицированного пользователя."""
    return current_user
