from datetime import timedelta
import uuid

from minio import Minio
from minio.error import S3Error

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


def validate_uploaded_media_object(
    *,
    storage_key: str,
    expected_content_type: str,
    allowed_content_types: set[str],
    max_size_bytes: int,
) -> None:
    try:
        stat = minio_client.stat_object(settings.s3_bucket_name, storage_key)
    except S3Error as exc:
        raise ValueError("Uploaded media object not found") from exc

    if stat.size is None or stat.size <= 0:
        raise ValueError("Uploaded media object is empty")

    if stat.size > max_size_bytes:
        raise ValueError("Uploaded media object is too large")

    if stat.content_type != expected_content_type:
        raise ValueError("Uploaded media content type does not match request")

    if stat.content_type not in allowed_content_types:
        raise ValueError("Uploaded media content type is not allowed")
