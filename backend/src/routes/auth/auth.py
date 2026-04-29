import hmac
import uuid

import jwt
from select import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette import status

from src.config import settings
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from src.models import User, RefreshSession
from src.routes.auth.security import get_password_hash, create_access_token, create_refresh_token, hash_refresh_token, \
    get_refresh_expires_at, decode_refresh_token, utc_now
from src.routes.auth.utils import get_user_by_username, authenticate_user, get_client_ip, set_refresh_cookie, \
    delete_refresh_cookie
from src.schemas.auth import RegisterRequest, LoginRequest, LoginResponse
from src.schemas.token import TokenResponse
from src.schemas.user import UserResponse
from src.session import get_session

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
        data: LoginRequest,
        request: Request,
        response: Response,
        session: AsyncSession = Depends(get_session),
):
    user = await authenticate_user(session, data.username, data.password)

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
    refresh_token = create_refresh_token(user, refresh_jti)
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


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
        request: Request,
        response: Response,
        session: AsyncSession = Depends(get_session),
):
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

    result = await session.execute(
        select(RefreshSession)
        .where(RefreshSession.refresh_jti == refresh_jti)
    )
    old_session = result.scalar_one_or_none()

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

    now = utc_now()

    if old_session.revoked_at is not None:
        delete_refresh_cookie(response)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token was already used or revoked",
        )

    if old_session.expires_at <= now:
        old_session.revoked_at = now
        await session.commit()
        delete_refresh_cookie(response)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh session expired",
        )

    expected_hash = hash_refresh_token(refresh_token)

    if not hmac.compare_digest(old_session.refresh_hash, expected_hash):
        delete_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token hash mismatch",
        )

    user = await session.get(User, user_id)

    if user is None or not user.is_active:
        old_session.revoked_at = now
        await session.commit()
        delete_refresh_cookie(response)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
        )

    # 1. Отзываем старую refresh-сессию
    old_session.revoked_at = now

    # 2. Создаём новую refresh-сессию
    new_refresh_jti = uuid.uuid4()
    new_refresh_token = create_refresh_token(user, new_refresh_jti)
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

    await session.commit()

    set_refresh_cookie(response, new_refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    refresh_token = request.cookies.get(settings.refresh_cookie_name)

    if refresh_token:
        try:
            payload = decode_refresh_token(refresh_token)

            if payload.get("type") == "refresh":
                refresh_jti = uuid.UUID(payload["jti"])

                result = await session.execute(
                    select(RefreshSession)
                    .where(RefreshSession.refresh_jti == refresh_jti)
                )
                refresh_session = result.scalar_one_or_none()

                if refresh_session and refresh_session.revoked_at is None:
                    refresh_session.revoked_at = utc_now()
                    await session.commit()

        except Exception:
            # logout не должен падать из-за плохой cookie
            pass

    delete_refresh_cookie(response)

    return {"detail": "Logged out"}
