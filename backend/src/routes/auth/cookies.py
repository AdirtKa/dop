"""Хелперы для установки и удаления auth-cookie."""

from fastapi import Response

from src.config import settings


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Устанавливает refresh-token в HTTP-only cookie."""
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path=settings.refresh_cookie_path,
        max_age=settings.jwt_refresh_expires,
    )


def delete_refresh_cookie(response: Response) -> None:
    """Удаляет refresh-cookie из ответа."""
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        domain=settings.cookie_domain,
        path=settings.refresh_cookie_path,
    )
