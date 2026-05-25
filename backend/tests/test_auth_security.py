from __future__ import annotations

# ruff: noqa: S105
from datetime import UTC, datetime, timedelta
import uuid

import jwt
import pytest

from src.config import settings
from src.routes.auth.client import get_client_ip
from src.routes.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    get_password_hash,
    hash_refresh_token,
    verify_password,
)
from tests.conftest import make_request


def test_access_token_round_trip_contains_expected_claims(active_user) -> None:
    token = create_access_token(active_user)

    payload = decode_access_token(token)

    assert payload["sub"] == str(active_user.id)
    assert payload["role"] == active_user.role.value
    assert payload["type"] == "access"
    assert payload["exp"] >= payload["iat"]


def test_refresh_token_round_trip_contains_session_identity(active_user) -> None:
    refresh_jti = uuid.uuid4()

    token = create_refresh_token(active_user.id, refresh_jti)
    payload = decode_refresh_token(token)

    assert payload["sub"] == str(active_user.id)
    assert payload["jti"] == str(refresh_jti)
    assert payload["type"] == "refresh"


def test_decode_refresh_token_rejects_missing_required_claim(active_user) -> None:
    payload = {
        "sub": str(active_user.id),
        "type": "refresh",
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    token = jwt.encode(
        payload,
        settings.refresh_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.MissingRequiredClaimError):
        decode_refresh_token(token)


def test_password_hash_verification_distinguishes_valid_and_invalid_password() -> None:
    password_hash = get_password_hash("correct horse battery staple")

    assert verify_password("correct horse battery staple", password_hash) is True
    assert verify_password("wrong password", password_hash) is False


def test_hash_refresh_token_is_deterministic_and_not_plaintext() -> None:
    token = "refresh-token-value"

    first_hash = hash_refresh_token(token)
    second_hash = hash_refresh_token(token)

    assert first_hash == second_hash
    assert first_hash != token
    assert len(first_hash) == 64


def test_refresh_cookie_path_includes_api_prefix(monkeypatch) -> None:
    monkeypatch.setattr(settings, "api_prefix", "/api")

    assert settings.refresh_cookie_path == "/api/auth"


def test_get_client_ip_prefers_forwarded_header_when_proxy_is_trusted(monkeypatch) -> None:
    monkeypatch.setattr(settings, "trust_proxy_headers", True)
    request = make_request(
        headers={"x-forwarded-for": "198.51.100.1, 10.0.0.2"},
        client_host="203.0.113.55",
    )

    assert get_client_ip(request) == "198.51.100.1"


def test_get_client_ip_falls_back_to_socket_address_when_proxy_not_trusted(monkeypatch) -> None:
    monkeypatch.setattr(settings, "trust_proxy_headers", False)
    request = make_request(
        headers={"x-forwarded-for": "198.51.100.1"},
        client_host="203.0.113.55",
    )

    assert get_client_ip(request) == "203.0.113.55"
