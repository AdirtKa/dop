"""Точка входа FastAPI-приложения и настройка middleware."""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from src.config import settings
from src.routes import auth_router, employee_router, root_router

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


def main() -> None:
    """Запускает приложение через Uvicorn."""
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
