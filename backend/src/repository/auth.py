"""Репозиторий для запросов, связанных с аутентификацией."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.refresh_session import RefreshSession
from src.models.user import User


async def get_user_by_username(
    session: AsyncSession,
    username: str,
) -> User | None:
    """Ищет пользователя по имени пользователя."""
    result = await session.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


async def get_refresh_session_by_jti(
    session: AsyncSession,
    refresh_jti: uuid.UUID,
    *,
    for_update: bool = False,
) -> RefreshSession | None:
    """Возвращает refresh-сессию по `jti`, при необходимости блокируя строку."""
    stmt = select(RefreshSession).where(RefreshSession.refresh_jti == refresh_jti)

    if for_update:
        stmt = stmt.with_for_update()

    result = await session.execute(stmt)
    return result.scalar_one_or_none()
