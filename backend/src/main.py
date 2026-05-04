"""Точка входа FastAPI-приложения и настройка middleware."""

import time

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from src.config import settings
from src.logger import get_access_logger, get_error_logger, get_request_client, setup_logging
from src.routes import auth_router, employee_router, root_router

setup_logging()
access_logger = get_access_logger()
error_logger = get_error_logger()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    employee_router,
    prefix=f"{settings.normalized_api_prefix}/employee",
    tags=["employee"],
)
app.include_router(auth_router, prefix=f"{settings.normalized_api_prefix}/auth", tags=["auth"])
app.include_router(root_router, prefix="")


@app.middleware("http")
async def log_requests(request, call_next):
    """Пишет каждое обращение к API в access.log."""
    started_at = time.perf_counter()
    client_ip = get_request_client(request)

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        access_logger.info(
            'method=%s path="%s" status=500 client=%s duration_ms=%s',
            request.method,
            request.url.path,
            client_ip,
            duration_ms,
        )
        raise

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    access_logger.info(
        'method=%s path="%s" status=%s client=%s duration_ms=%s',
        request.method,
        request.url.path,
        response.status_code,
        client_ip,
        duration_ms,
    )
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    """Логирует неожиданные исключения и возвращает 500 без внутренностей."""
    error_logger.exception(
        'Unhandled error during %s "%s" from client=%s',
        request.method,
        request.url.path,
        get_request_client(request),
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


def main() -> None:
    """Запускает приложение через Uvicorn."""
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
