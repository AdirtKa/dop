from datetime import timedelta

from minio import Minio

from src.config import settings

minio_client = Minio(
    settings.s3_endpoint_url.removeprefix(r"http://").removeprefix(r"https://"),
    access_key=settings.s3_access_key,
    secret_key=settings.s3_secret_key.get_secret_value(),
    secure=False,
)


def get_presigned_put_url(bucket_name, object_name) -> str:
    upload_url: str = minio_client.get_presigned_url(
        bucket_name=bucket_name,
        object_name=object_name,
        expires=timedelta(minutes=15),
        method="PUT",
    )
    return upload_url
