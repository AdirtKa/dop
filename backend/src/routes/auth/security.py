import hashlib
import hmac

import jwt
import uuid
from datetime import datetime, UTC, timedelta
from typing import Any

from pwdlib import PasswordHash

from src.config import settings
from src.models import User

password_hash = PasswordHash.recommended()


def utc_now() -> datetime:
    return datetime.now(UTC)


def create_refresh_token(user_id: uuid.UUID, jti: uuid.UUID) -> str:
    expires = utc_now() + timedelta(seconds=settings.jwt_refresh_expires)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "jti": str(jti),
        "type": "refresh",
        "exp": expires,
        "iat": datetime.now(UTC),
    }

    return jwt.encode(payload, settings.refresh_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm)


def hash_refresh_token(refresh_token: str) -> str:
    return hmac.new(
        settings.refresh_secret_key.get_secret_value().encode("utf-8"),
        refresh_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def create_access_token(user: User) -> str:
    now = utc_now()
    expire = now + timedelta(seconds=settings.jwt_access_expires)

    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "type": "access",
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.access_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.access_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={
            "require": ["sub", "type", "exp", "iat"],
        },
    )


def decode_refresh_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.refresh_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={
            "require": ["sub", "jti", "type", "exp", "iat"],
        },
    )


def get_refresh_expires_at() -> datetime:
    return utc_now() + timedelta(seconds=settings.jwt_refresh_expires)


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)
