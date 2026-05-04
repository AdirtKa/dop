"""Сервисный слой для сценариев аутентификации и refresh-token rotation."""

import hmac
import uuid

from fastapi import HTTPException, Request, Response
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.config import settings
from src.logger import get_error_logger
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

error_logger = get_error_logger()


def _reject_refresh(
    response: Response,
    client_ip: str,
    detail: str,
    *,
    refresh_jti: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    exc: Exception | None = None,
) -> None:
    """Логирует причину отказа refresh-запроса, чистит cookie и бросает 401."""
    delete_refresh_cookie(response)

    log_parts = [f"Refresh rejected from client={client_ip}: {detail}"]
    if refresh_jti is not None:
        log_parts.append(f"jti={refresh_jti}")
    if user_id is not None:
        log_parts.append(f"user_id={user_id}")

    error_logger.warning(" ".join(log_parts), exc_info=exc)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
    ) from exc


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
    client_ip = get_client_ip(request)

    if user is None:
        error_logger.warning(
            'Login failed for username="%s" from client=%s: invalid credentials',
            username,
            client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        error_logger.warning(
            'Login blocked for user_id=%s username="%s" from client=%s: inactive user',
            user.id,
            user.username,
            client_ip,
        )
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
        ip_address=client_ip,
        expires_at=get_refresh_expires_at(),
    )

    session.add(refresh_session)
    await session.commit()

    set_refresh_cookie(response, refresh_token)
    error_logger.info(
        'Login succeeded for user_id=%s username="%s" from client=%s',
        user.id,
        user.username,
        client_ip,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",  # noqa S106
        user=UserResponse.model_validate(user),
    )


async def refresh_tokens(
    session: AsyncSession,
    request: Request,
    response: Response,
) -> TokenResponse:
    """Выполняет refresh access-token и ротацию refresh-token."""
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    client_ip = get_client_ip(request)

    if not refresh_token:
        _reject_refresh(response, client_ip, "Missing refresh token")

    try:
        payload = decode_refresh_token(refresh_token)

        if payload.get("type") != "refresh":
            _reject_refresh(response, client_ip, "Invalid token type")

        user_id = uuid.UUID(payload["sub"])
        refresh_jti = uuid.UUID(payload["jti"])

    except (jwt.InvalidTokenError, ValueError, KeyError) as exc:
        _reject_refresh(response, client_ip, "Invalid refresh token", exc=exc)

    expected_hash = hash_refresh_token(refresh_token)
    now = utc_now()

    async with session.begin():
        old_session = await get_refresh_session_by_jti(
            session,
            refresh_jti,
            for_update=True,
        )

        if old_session is None:
            _reject_refresh(
                response,
                client_ip,
                "Unknown refresh session",
                refresh_jti=refresh_jti,
            )

        if old_session.user_id != user_id:
            _reject_refresh(
                response,
                client_ip,
                "Refresh session mismatch",
                refresh_jti=refresh_jti,
            )

        if old_session.revoked_at is not None:
            _reject_refresh(
                response,
                client_ip,
                "Refresh token was already used or revoked",
                refresh_jti=refresh_jti,
            )

        if old_session.expires_at <= now:
            old_session.revoked_at = now
            _reject_refresh(
                response,
                client_ip,
                "Refresh session expired",
                refresh_jti=refresh_jti,
            )

        if not hmac.compare_digest(old_session.refresh_hash, expected_hash):
            old_session.revoked_at = now
            _reject_refresh(
                response,
                client_ip,
                "Refresh token hash mismatch",
                refresh_jti=refresh_jti,
            )

        user = await session.get(User, user_id)

        if user is None or not user.is_active:
            old_session.revoked_at = now
            _reject_refresh(
                response,
                client_ip,
                "User is inactive",
                user_id=user_id,
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
            ip_address=client_ip,
            expires_at=get_refresh_expires_at(),
        )

        old_session.replaced_by_jti = new_refresh_jti
        session.add(new_session)

    new_access_token = create_access_token(user)
    set_refresh_cookie(response, new_refresh_token)
    error_logger.info(
        "Refresh succeeded for user_id=%s from client=%s",
        user.id,
        client_ip,
    )

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",  # noqa S106
    )


async def logout_user(
    session: AsyncSession,
    request: Request,
    response: Response,
) -> dict[str, str]:
    """Отзывает refresh-сессию пользователя и очищает cookie."""
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    client_ip = get_client_ip(request)

    if refresh_token:
        try:
            payload = decode_refresh_token(refresh_token)

            if payload.get("type") == "refresh":
                refresh_jti = uuid.UUID(payload["jti"])
                refresh_session = await get_refresh_session_by_jti(session, refresh_jti)

                if refresh_session and refresh_session.revoked_at is None:
                    refresh_session.revoked_at = utc_now()
                    await session.commit()
                    error_logger.info(
                        "Logout succeeded for user_id=%s from client=%s",
                        refresh_session.user_id,
                        client_ip,
                    )

        except Exception as exc:
            error_logger.warning(
                "Logout cleanup failed for client=%s",
                client_ip,
                exc_info=exc,
            )

    delete_refresh_cookie(response)
    return {"detail": "Logged out"}
