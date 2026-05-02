"""Точка входа FastAPI-приложения и настройка middleware."""

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.config import settings
from src.routes import root_router, employee_router, auth_router

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
app.include_router(
    auth_router, prefix=f"{settings.normalized_api_prefix}/auth", tags=["auth"]
)
app.include_router(root_router, prefix="")


def main() -> None:
    """Запускает приложение через Uvicorn."""
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
