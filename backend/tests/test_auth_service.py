from __future__ import annotations

# ruff: noqa: S105, S106, ARG005
from datetime import timedelta
from unittest.mock import AsyncMock
import uuid

from fastapi import HTTPException
import jwt
import pytest

from src.config import settings
from src.models.refresh_session import RefreshSession
from src.routes.auth.security import get_password_hash
from src.services import auth as auth_service
from tests.conftest import FakeSession, make_request


@pytest.mark.asyncio
async def test_authenticate_user_returns_user_for_valid_credentials(
    monkeypatch, active_user
) -> None:
    session = object()
    active_user.password_hash = get_password_hash("correct-password")
    monkeypatch.setattr(
        auth_service,
        "get_user_by_username",
        AsyncMock(return_value=active_user),
    )

    user = await auth_service.authenticate_user(
        session,
        active_user.username,
        "correct-password",
    )

    assert user is active_user


@pytest.mark.asyncio
async def test_authenticate_user_returns_none_for_wrong_password(monkeypatch, active_user) -> None:
    monkeypatch.setattr(
        auth_service,
        "get_user_by_username",
        AsyncMock(return_value=active_user),
    )
    monkeypatch.setattr(auth_service, "verify_password", lambda plain, hashed: False)

    user = await auth_service.authenticate_user(
        object(),
        active_user.username,
        "wrong-password",
    )

    assert user is None


@pytest.mark.asyncio
async def test_login_user_creates_refresh_session_and_cookie(
    monkeypatch, active_user, response, now
) -> None:
    session = FakeSession()
    refresh_jti = uuid.uuid4()
    expires_at = now + timedelta(days=1)
    request = make_request(
        headers={"user-agent": "pytest-browser"},
        client_host="198.51.100.77",
    )

    monkeypatch.setattr(
        auth_service,
        "authenticate_user",
        AsyncMock(return_value=active_user),
    )
    monkeypatch.setattr(auth_service, "create_access_token", lambda user: "access-token")
    monkeypatch.setattr(
        auth_service,
        "create_refresh_token",
        lambda user_id, jti: "refresh-token",
    )
    monkeypatch.setattr(
        auth_service,
        "hash_refresh_token",
        lambda token: "hashed-refresh-token",
    )
    monkeypatch.setattr(auth_service, "get_refresh_expires_at", lambda: expires_at)
    monkeypatch.setattr(auth_service.uuid, "uuid4", lambda: refresh_jti)

    result = await auth_service.login_user(
        session=session,
        request=request,
        response=response,
        username=active_user.username,
        password="correct-password",
    )

    assert result.access_token == "access-token"
    assert result.user.id == active_user.id
    assert session.commit.await_count == 1
    assert len(session.added) == 1
    saved_session = session.added[0]
    assert isinstance(saved_session, RefreshSession)
    assert saved_session.user_id == active_user.id
    assert saved_session.refresh_jti == refresh_jti
    assert saved_session.refresh_hash == "hashed-refresh-token"
    assert saved_session.user_agent == "pytest-browser"
    assert saved_session.ip_address == "198.51.100.77"
    assert saved_session.expires_at == expires_at
    assert "refresh-token" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]


@pytest.mark.asyncio
async def test_login_user_rejects_unknown_credentials(monkeypatch, response) -> None:
    session = FakeSession()
    request = make_request()
    monkeypatch.setattr(
        auth_service,
        "authenticate_user",
        AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException) as exc:
        await auth_service.login_user(
            session=session,
            request=request,
            response=response,
            username="ghost",
            password="bad-password",
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid username or password"
    session.commit.assert_not_awaited()
    assert session.added == []
    assert "set-cookie" not in response.headers


@pytest.mark.asyncio
async def test_login_user_rejects_inactive_user(monkeypatch, inactive_user, response) -> None:
    session = FakeSession()
    request = make_request()
    monkeypatch.setattr(
        auth_service,
        "authenticate_user",
        AsyncMock(return_value=inactive_user),
    )

    with pytest.raises(HTTPException) as exc:
        await auth_service.login_user(
            session=session,
            request=request,
            response=response,
            username=inactive_user.username,
            password="correct-password",
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "User is inactive"
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_refresh_tokens_rotates_session_and_issues_new_cookie(
    monkeypatch,
    active_user,
    refresh_session,
    response,
    now,
) -> None:
    session = FakeSession(user=active_user)
    new_refresh_jti = uuid.uuid4()
    request = make_request(
        path="/api/auth/refresh",
        headers={"user-agent": "pytest-browser"},
        cookies={settings.refresh_cookie_name: "old-refresh-token"},
        client_host="198.51.100.88",
    )

    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: {
            "sub": str(active_user.id),
            "jti": str(refresh_session.refresh_jti),
            "type": "refresh",
        },
    )
    monkeypatch.setattr(
        auth_service,
        "get_refresh_session_by_jti",
        AsyncMock(return_value=refresh_session),
    )
    monkeypatch.setattr(auth_service, "utc_now", lambda: now)
    monkeypatch.setattr(
        auth_service,
        "create_refresh_token",
        lambda user_id, jti: "new-refresh-token",
    )
    monkeypatch.setattr(auth_service, "create_access_token", lambda user: "new-access-token")
    monkeypatch.setattr(
        auth_service,
        "get_refresh_expires_at",
        lambda: now + timedelta(days=1),
    )
    monkeypatch.setattr(auth_service.uuid, "uuid4", lambda: new_refresh_jti)

    def hash_side_effect(token: str) -> str:
        if token == "old-refresh-token":
            return refresh_session.refresh_hash
        if token == "new-refresh-token":
            return "new-refresh-hash"
        raise AssertionError(f"Unexpected token: {token}")

    monkeypatch.setattr(auth_service, "hash_refresh_token", hash_side_effect)

    result = await auth_service.refresh_tokens(
        session=session,
        request=request,
        response=response,
    )

    assert result.access_token == "new-access-token"
    assert refresh_session.revoked_at == now
    assert refresh_session.replaced_by_jti == new_refresh_jti
    assert len(session.added) == 1
    new_session = session.added[0]
    assert new_session.user_id == active_user.id
    assert new_session.refresh_jti == new_refresh_jti
    assert new_session.refresh_hash == "new-refresh-hash"
    assert new_session.ip_address == "198.51.100.88"
    assert new_session.user_agent == "pytest-browser"
    assert "new-refresh-token" in response.headers["set-cookie"]


@pytest.mark.asyncio
async def test_refresh_tokens_rejects_missing_cookie(response) -> None:
    session = FakeSession()
    request = make_request(path="/api/auth/refresh")

    with pytest.raises(HTTPException) as exc:
        await auth_service.refresh_tokens(session=session, request=request, response=response)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Missing refresh token"
    assert settings.refresh_cookie_name in response.headers["set-cookie"]


@pytest.mark.asyncio
async def test_refresh_tokens_rejects_invalid_refresh_token(monkeypatch, response) -> None:
    session = FakeSession()
    request = make_request(
        path="/api/auth/refresh",
        cookies={settings.refresh_cookie_name: "broken-refresh-token"},
    )

    def raise_invalid(_: str) -> dict[str, str]:
        raise jwt.InvalidTokenError("invalid")

    monkeypatch.setattr(auth_service, "decode_refresh_token", raise_invalid)

    with pytest.raises(HTTPException) as exc:
        await auth_service.refresh_tokens(session=session, request=request, response=response)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid refresh token"
    assert settings.refresh_cookie_name in response.headers["set-cookie"]


@pytest.mark.asyncio
async def test_refresh_tokens_rejects_non_refresh_token_type(
    monkeypatch, active_user, response
) -> None:
    session = FakeSession()
    request = make_request(
        path="/api/auth/refresh",
        cookies={settings.refresh_cookie_name: "wrong-type-token"},
    )
    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: {
            "sub": str(active_user.id),
            "jti": str(uuid.uuid4()),
            "type": "access",
        },
    )

    with pytest.raises(HTTPException) as exc:
        await auth_service.refresh_tokens(session=session, request=request, response=response)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token type"


@pytest.mark.asyncio
async def test_refresh_tokens_rejects_reused_refresh_token(
    monkeypatch,
    active_user,
    refresh_session,
    response,
) -> None:
    session = FakeSession(user=active_user)
    refresh_session.revoked_at = refresh_session.expires_at
    request = make_request(
        path="/api/auth/refresh",
        cookies={settings.refresh_cookie_name: "replayed-refresh-token"},
    )
    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: {
            "sub": str(active_user.id),
            "jti": str(refresh_session.refresh_jti),
            "type": "refresh",
        },
    )
    monkeypatch.setattr(
        auth_service,
        "get_refresh_session_by_jti",
        AsyncMock(return_value=refresh_session),
    )
    monkeypatch.setattr(
        auth_service, "hash_refresh_token", lambda token: refresh_session.refresh_hash
    )
    monkeypatch.setattr(
        auth_service,
        "utc_now",
        lambda: refresh_session.expires_at - timedelta(minutes=1),
    )

    with pytest.raises(HTTPException) as exc:
        await auth_service.refresh_tokens(session=session, request=request, response=response)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Refresh token was already used or revoked"


@pytest.mark.asyncio
async def test_refresh_tokens_revokes_expired_session(
    monkeypatch,
    active_user,
    refresh_session,
    response,
    now,
) -> None:
    session = FakeSession(user=active_user)
    refresh_session.expires_at = now
    request = make_request(
        path="/api/auth/refresh",
        cookies={settings.refresh_cookie_name: "expired-refresh-token"},
    )
    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: {
            "sub": str(active_user.id),
            "jti": str(refresh_session.refresh_jti),
            "type": "refresh",
        },
    )
    monkeypatch.setattr(
        auth_service,
        "get_refresh_session_by_jti",
        AsyncMock(return_value=refresh_session),
    )
    monkeypatch.setattr(
        auth_service, "hash_refresh_token", lambda token: refresh_session.refresh_hash
    )
    monkeypatch.setattr(auth_service, "utc_now", lambda: now)

    with pytest.raises(HTTPException) as exc:
        await auth_service.refresh_tokens(session=session, request=request, response=response)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Refresh session expired"
    assert refresh_session.revoked_at == now


@pytest.mark.asyncio
async def test_refresh_tokens_revokes_session_on_hash_mismatch(
    monkeypatch,
    active_user,
    refresh_session,
    response,
    now,
) -> None:
    session = FakeSession(user=active_user)
    request = make_request(
        path="/api/auth/refresh",
        cookies={settings.refresh_cookie_name: "tampered-refresh-token"},
    )
    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: {
            "sub": str(active_user.id),
            "jti": str(refresh_session.refresh_jti),
            "type": "refresh",
        },
    )
    monkeypatch.setattr(
        auth_service,
        "get_refresh_session_by_jti",
        AsyncMock(return_value=refresh_session),
    )
    monkeypatch.setattr(auth_service, "hash_refresh_token", lambda token: "unexpected-hash")
    monkeypatch.setattr(auth_service, "utc_now", lambda: now)

    with pytest.raises(HTTPException) as exc:
        await auth_service.refresh_tokens(session=session, request=request, response=response)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Refresh token hash mismatch"
    assert refresh_session.revoked_at == now


@pytest.mark.asyncio
async def test_refresh_tokens_revokes_session_for_inactive_user(
    monkeypatch,
    inactive_user,
    refresh_session,
    response,
    now,
) -> None:
    session = FakeSession(user=inactive_user)
    refresh_session.user_id = inactive_user.id
    request = make_request(
        path="/api/auth/refresh",
        cookies={settings.refresh_cookie_name: "inactive-user-refresh-token"},
    )
    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: {
            "sub": str(inactive_user.id),
            "jti": str(refresh_session.refresh_jti),
            "type": "refresh",
        },
    )
    monkeypatch.setattr(
        auth_service,
        "get_refresh_session_by_jti",
        AsyncMock(return_value=refresh_session),
    )
    monkeypatch.setattr(
        auth_service, "hash_refresh_token", lambda token: refresh_session.refresh_hash
    )
    monkeypatch.setattr(auth_service, "utc_now", lambda: now)

    with pytest.raises(HTTPException) as exc:
        await auth_service.refresh_tokens(session=session, request=request, response=response)

    assert exc.value.status_code == 401
    assert exc.value.detail == "User is inactive"
    assert refresh_session.revoked_at == now


@pytest.mark.asyncio
async def test_logout_user_revokes_active_session_and_clears_cookie(
    monkeypatch,
    refresh_session,
    response,
    now,
) -> None:
    session = FakeSession()
    request = make_request(
        path="/api/auth/logout",
        cookies={settings.refresh_cookie_name: "logout-refresh-token"},
    )
    monkeypatch.setattr(
        auth_service,
        "decode_refresh_token",
        lambda token: {"jti": str(refresh_session.refresh_jti), "type": "refresh"},
    )
    monkeypatch.setattr(
        auth_service,
        "get_refresh_session_by_jti",
        AsyncMock(return_value=refresh_session),
    )
    monkeypatch.setattr(auth_service, "utc_now", lambda: now)

    result = await auth_service.logout_user(session=session, request=request, response=response)

    assert result == {"detail": "Logged out"}
    assert refresh_session.revoked_at == now
    assert session.commit.await_count == 1
    assert settings.refresh_cookie_name in response.headers["set-cookie"]


@pytest.mark.asyncio
async def test_logout_user_clears_cookie_even_when_token_is_invalid(monkeypatch, response) -> None:
    session = FakeSession()
    request = make_request(
        path="/api/auth/logout",
        cookies={settings.refresh_cookie_name: "bad-refresh-token"},
    )

    def raise_invalid(_: str) -> dict[str, str]:
        raise jwt.InvalidTokenError("bad token")

    monkeypatch.setattr(auth_service, "decode_refresh_token", raise_invalid)

    result = await auth_service.logout_user(session=session, request=request, response=response)

    assert result == {"detail": "Logged out"}
    session.commit.assert_not_awaited()
    assert settings.refresh_cookie_name in response.headers["set-cookie"]
