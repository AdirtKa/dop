"""Load data from .env file."""

from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"


class Settings(BaseSettings):
    """Base project settings."""

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

    jwt_secret_key: SecretStr = Field(
        alias="JWT_SECRET_KEY",
    )

    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_expires: int = Field(default=3600, alias="JWT_ACCESS_EXPIRES")
    jwt_refresh_expires: int = Field(default=86400, alias="JWT_REFRESH_EXPIRES")
    app_env: str = Field(default="dev", alias="APP_ENV")

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
        """Check if backend running in dev mode."""
        return self.app_env == "dev"

    @property
    def database_uri(self) -> str:
        """Backward compatible alias used by some modules."""
        return self.database_url


settings = Settings()