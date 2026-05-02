"""Загрузка и представление настроек приложения из `.env`."""

from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"


class Settings(BaseSettings):
    """Настройки backend-приложения."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(
        validation_alias=AliasChoices("DATABASE_URL", "db_url"),
        description="DSN Postgres",
    )

    access_secret_key: SecretStr = Field(
        alias="ACCESS_SECRET_KEY",
    )

    refresh_secret_key: SecretStr = Field(
        alias="REFRESH_SECRET_KEY",
    )

    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_expires: int = Field(default=3600, alias="JWT_ACCESS_EXPIRES")
    jwt_refresh_expires: int = Field(default=86400, alias="JWT_REFRESH_EXPIRES")
    app_env: str = Field(default="dev", alias="APP_ENV")
    api_prefix: str = Field(default="", alias="API_PREFIX")
    refresh_cookie_name: str = Field(
        default="refresh_cookie", alias="REFRESH_COOKIE_NAME"
    )
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    cookie_samesite: Literal["lax", "strict", "none"] = Field(
        default="lax", alias="COOKIE_SAMESITE"
    )
    cookie_domain: str | None = Field(default=None, alias="COOKIE_DOMAIN")
    cors_origins_raw: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )
    trust_proxy_headers: bool = Field(default=False, alias="TRUST_PROXY_HEADERS")

    s3_endpoint_url: str = Field(
        default="http://127.0.0.1:9000",
        alias="S3_ENDPOINT_URL",
    )

    s3_access_key: str = Field(
        default="dop_admin",
        alias="S3_ACCESS_KEY",
    )

    s3_secret_key: SecretStr = Field(
        default=SecretStr("dop_admin_password"),
        alias="S3_SECRET_KEY",
    )

    s3_bucket_name: str = Field(
        default="dop-media",
        alias="S3_BUCKET_NAME",
    )

    s3_public_url: str = Field(
        default="http://127.0.0.1:9000/dop-media",
        alias="S3_PUBLIC_URL",
    )

    @property
    def is_dev(self) -> bool:
        """Проверяет, запущено ли приложение в режиме разработки."""
        return self.app_env == "dev"

    @property
    def normalized_api_prefix(self) -> str:
        """Нормализует внешний префикс API."""
        prefix = self.api_prefix.strip()

        if not prefix:
            return ""

        prefix = prefix if prefix.startswith("/") else f"/{prefix}"
        return prefix.rstrip("/")

    @property
    def refresh_cookie_path(self) -> str:
        """Возвращает путь, на который должна быть привязана refresh-cookie."""
        return f"{self.normalized_api_prefix}/auth" or "/auth"

    @property
    def auth_token_url(self) -> str:
        """Возвращает URL логина для OpenAPI-схемы."""
        return f"{self.refresh_cookie_path}/login"

    @property
    def cors_origins(self) -> list[str]:
        """Разбирает список разрешённых CORS origin из переменной окружения."""
        return [
            origin.strip()
            for origin in self.cors_origins_raw.split(",")
            if origin.strip()
        ]

    @property
    def database_uri(self) -> str:
        """Возвращает обратнос совместимый алиас для URL базы данных."""
        return self.database_url


settings = Settings()
