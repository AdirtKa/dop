from __future__ import annotations

# ruff: noqa: E402, S106
from datetime import UTC, datetime, timedelta
import os
from pathlib import Path
import sys
from typing import Any
from unittest.mock import AsyncMock
import uuid

from fastapi import Response
import pytest
from starlette.requests import Request

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test_db")
os.environ.setdefault("ACCESS_SECRET_KEY", "test-access-secret-key-with-32-bytes")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret-key-with-32-bytes")

from src.models.refresh_session import RefreshSession
from src.models.user import User, UserRole


def make_request(
    *,
    method: str = "POST",
    path: str = "/api/auth/test",
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    client_host: str = "203.0.113.10",
) -> Request:
    raw_headers: list[tuple[bytes, bytes]] = []

    if headers:
        raw_headers.extend(
            (key.lower().encode("utf-8"), value.encode("utf-8")) for key, value in headers.items()
        )

    if cookies:
        cookie_value = "; ".join(f"{key}={value}" for key, value in cookies.items())
        raw_headers.append((b"cookie", cookie_value.encode("utf-8")))

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": raw_headers,
        "client": (client_host, 12345),
    }
    return Request(scope)


class DummyTransaction:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class FakeSession:
    def __init__(self, *, user: User | None = None) -> None:
        self.added: list[Any] = []
        self.commit = AsyncMock()
        self.get = AsyncMock(return_value=user)

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    def begin(self) -> DummyTransaction:
        return DummyTransaction()


@pytest.fixture
def active_user() -> User:
    return User(
        id=uuid.uuid4(),
        username="alice",
        password_hash="stored-hash",
        role=UserRole.ADMIN,
        is_active=True,
    )


@pytest.fixture
def inactive_user() -> User:
    return User(
        id=uuid.uuid4(),
        username="bob",
        password_hash="stored-hash",
        role=UserRole.EMPLOYEE,
        is_active=False,
    )


@pytest.fixture
def response() -> Response:
    return Response()


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 5, 4, 12, 0, tzinfo=UTC)


@pytest.fixture
def refresh_session(active_user: User, now: datetime) -> RefreshSession:
    return RefreshSession(
        user_id=active_user.id,
        refresh_jti=uuid.uuid4(),
        refresh_hash="expected-refresh-hash",
        user_agent="pytest",
        ip_address="198.51.100.7",
        expires_at=now + timedelta(hours=1),
    )
