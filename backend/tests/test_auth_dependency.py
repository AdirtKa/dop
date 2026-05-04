from __future__ import annotations

from unittest.mock import AsyncMock

# ruff: noqa: S106, ARG005
import uuid

from fastapi import HTTPException
import jwt
import pytest

from src.models.user import UserRole
from src.routes.auth import dependency as auth_dependency


@pytest.mark.asyncio
async def test_get_current_user_returns_active_user(monkeypatch, active_user) -> None:
    session = type("Session", (), {})()
    session.get = AsyncMock(return_value=active_user)
    monkeypatch.setattr(
        auth_dependency,
        "decode_access_token",
        lambda token: {"sub": str(active_user.id), "type": "access"},
    )

    user = await auth_dependency.get_current_user(token="valid-token", session=session)

    assert user is active_user
    session.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_current_user_rejects_non_access_token(monkeypatch) -> None:
    session = type("Session", (), {})()
    session.get = AsyncMock()
    monkeypatch.setattr(
        auth_dependency,
        "decode_access_token",
        lambda token: {"sub": str(uuid.uuid4()), "type": "refresh"},
    )

    with pytest.raises(HTTPException) as exc:
        await auth_dependency.get_current_user(token="wrong-type", session=session)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Could not validate credentials"
    session.get.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_payload(monkeypatch) -> None:
    session = type("Session", (), {})()
    session.get = AsyncMock()

    def raise_invalid(_: str) -> dict[str, str]:
        raise jwt.InvalidTokenError("bad token")

    monkeypatch.setattr(auth_dependency, "decode_access_token", raise_invalid)

    with pytest.raises(HTTPException) as exc:
        await auth_dependency.get_current_user(token="bad-token", session=session)

    assert exc.value.status_code == 401
    session.get.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_current_user_rejects_inactive_user(monkeypatch, inactive_user) -> None:
    session = type("Session", (), {})()
    session.get = AsyncMock(return_value=inactive_user)
    monkeypatch.setattr(
        auth_dependency,
        "decode_access_token",
        lambda token: {"sub": str(inactive_user.id), "type": "access"},
    )

    with pytest.raises(HTTPException) as exc:
        await auth_dependency.get_current_user(
            token="inactive-user-token",
            session=session,
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "Could not validate credentials"


@pytest.mark.asyncio
async def test_require_roles_allows_expected_role(active_user) -> None:
    checker = auth_dependency.require_roles(UserRole.ADMIN, UserRole.ORGANIZATION)

    user = await checker(current_user=active_user)

    assert user is active_user


@pytest.mark.asyncio
async def test_require_roles_rejects_forbidden_role(active_user) -> None:
    checker = auth_dependency.require_roles(UserRole.ORGANIZATION)

    with pytest.raises(HTTPException) as exc:
        await checker(current_user=active_user)

    assert exc.value.status_code == 403
    assert exc.value.detail == "Not enough permissions"
