from datetime import timedelta
import uuid

from minio import Minio

from src.config import settings
from src.models import MediaKind


def get_media_kind_by_content_type(content_type: str) -> MediaKind:
    """Определяет тип медиа по MIME-типу."""

    if content_type.startswith("image/"):
        return MediaKind.image

    if content_type.startswith("video/"):
        return MediaKind.video

    raise ValueError("Unsupported media content type")


minio_client = Minio(
    settings.s3_endpoint_url.removeprefix(r"http://").removeprefix(r"https://"),
    access_key=settings.s3_access_key,
    secret_key=settings.s3_secret_key.get_secret_value(),
    secure=False,
)


def build_media_payload(
    *,
    filename: str,
    storage_prefix: str,
) -> tuple[str, str, str]:
    """Генерирует ключ хранения и URL-адреса для загрузки медиа файла."""
    ext: str = filename.rsplit(".", maxsplit=1)[-1]
    storage_key: str = f"{storage_prefix}/{uuid.uuid4()}.{ext}"
    presigned_url: str = get_presigned_put_url(settings.s3_bucket_name, storage_key)
    public_url: str = f"{settings.s3_public_url}/{storage_key}"
    return storage_key, presigned_url, public_url


def get_presigned_put_url(bucket_name, object_name) -> str:
    upload_url: str = minio_client.get_presigned_url(
        bucket_name=bucket_name,
        object_name=object_name,
        expires=timedelta(minutes=15),
        method="PUT",
    )
    return upload_url
