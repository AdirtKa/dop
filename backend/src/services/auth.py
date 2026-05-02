"""Сервисный слой для сценариев аутентификации и refresh-token rotation."""

import hmac
import uuid

import jwt
from fastapi import HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.config import settings
from src.models.refresh_session import RefreshSession
from src.models.user import User
from src.repository.auth import get_refresh_session_by_jti, get_user_by_username
from src.routes.auth.client import get_client_ip
from src.routes.auth.cookies import delete_refresh_cookie, set_refresh_cookie
from src.routes.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_refresh_expires_at,
    hash_refresh_token,
    utc_now,
    verify_password,
)
from src.schemas.auth import LoginResponse
from src.schemas.token import TokenResponse
from src.schemas.user import UserResponse


async def authenticate_user(
    session: AsyncSession,
    username: str,
    password: str,
) -> User | None:
    """Проверяет логин и пароль пользователя."""
    user = await get_user_by_username(session, username)

    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


async def login_user(
    session: AsyncSession,
    request: Request,
    response: Response,
    username: str,
    password: str,
) -> LoginResponse:
    """Аутентифицирует пользователя и создаёт новую refresh-сессию."""
    user = await authenticate_user(session, username, password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    access_token = create_access_token(user)

    refresh_jti = uuid.uuid4()
    refresh_token = create_refresh_token(user.id, refresh_jti)
    refresh_hash = hash_refresh_token(refresh_token)

    refresh_session = RefreshSession(
        user_id=user.id,
        refresh_jti=refresh_jti,
        refresh_hash=refresh_hash,
        user_agent=request.headers.get("user-agent"),
        ip_address=get_client_ip(request),
        expires_at=get_refresh_expires_at(),
    )

    session.add(refresh_session)
    await session.commit()

    set_refresh_cookie(response, refresh_token)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


async def refresh_tokens(
    session: AsyncSession,
    request: Request,
    response: Response,
) -> TokenResponse:
    """Выполняет refresh access-token и ротацию refresh-token."""
    refresh_token = request.cookies.get(settings.refresh_cookie_name)

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    try:
        payload = decode_refresh_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = uuid.UUID(payload["sub"])
        refresh_jti = uuid.UUID(payload["jti"])

    except (jwt.InvalidTokenError, ValueError, KeyError):
        delete_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    expected_hash = hash_refresh_token(refresh_token)
    now = utc_now()

    async with session.begin():
        old_session = await get_refresh_session_by_jti(
            session,
            refresh_jti,
            for_update=True,
        )

        if old_session is None:
            delete_refresh_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unknown refresh session",
            )

        if old_session.user_id != user_id:
            delete_refresh_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh session mismatch",
            )

        if old_session.revoked_at is not None:
            delete_refresh_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token was already used or revoked",
            )

        if old_session.expires_at <= now:
            old_session.revoked_at = now
            delete_refresh_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh session expired",
            )

        if not hmac.compare_digest(old_session.refresh_hash, expected_hash):
            old_session.revoked_at = now
            delete_refresh_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token hash mismatch",
            )

        user = await session.get(User, user_id)

        if user is None or not user.is_active:
            old_session.revoked_at = now
            delete_refresh_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive",
            )

        old_session.revoked_at = now

        new_refresh_jti = uuid.uuid4()
        new_refresh_token = create_refresh_token(user.id, new_refresh_jti)
        new_refresh_hash = hash_refresh_token(new_refresh_token)

        new_session = RefreshSession(
            user_id=user.id,
            refresh_jti=new_refresh_jti,
            refresh_hash=new_refresh_hash,
            user_agent=request.headers.get("user-agent"),
            ip_address=get_client_ip(request),
            expires_at=get_refresh_expires_at(),
        )

        old_session.replaced_by_jti = new_refresh_jti
        session.add(new_session)

    new_access_token = create_access_token(user)
    set_refresh_cookie(response, new_refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
    )


async def logout_user(
    session: AsyncSession,
    request: Request,
    response: Response,
) -> dict[str, str]:
    """Отзывает refresh-сессию пользователя и очищает cookie."""
    refresh_token = request.cookies.get(settings.refresh_cookie_name)

    if refresh_token:
        try:
            payload = decode_refresh_token(refresh_token)

            if payload.get("type") == "refresh":
                refresh_jti = uuid.UUID(payload["jti"])
                refresh_session = await get_refresh_session_by_jti(session, refresh_jti)

                if refresh_session and refresh_session.revoked_at is None:
                    refresh_session.revoked_at = utc_now()
                    await session.commit()

        except Exception:
            pass

    delete_refresh_cookie(response)
    return {"detail": "Logged out"}
