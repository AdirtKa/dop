from fastapi import Request

from src.config import settings


def get_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for") if settings.trust_proxy_headers else None
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return None
