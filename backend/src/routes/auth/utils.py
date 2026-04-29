from fastapi import Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models import User
from .security import verify_password


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path=settings.refresh_cookie_path,
        max_age=settings.jwt_refresh_expires,
    )


def delete_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=settings.refresh_cookie_path,
    )


async def get_user_by_username(
    session: AsyncSession,
    username: str,
) -> User | None:
    result = await session.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


async def authenticate_user(
    session: AsyncSession,
    username: str,
    password: str,
) -> User | None:
    user = await get_user_by_username(session, username)

    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def get_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return None

