from __future__ import annotations

from dataclasses import dataclass

from minio.error import S3Error
import pytest

from src.services import media as media_service


@dataclass
class StatObjectStub:
    size: int | None
    content_type: str | None


class PresignClientStub:
    def __init__(self, endpoint_url: str) -> None:
        self.endpoint_url = endpoint_url
        self.kwargs: dict[str, object] | None = None

    def get_presigned_url(self, **kwargs: object) -> str:
        self.kwargs = kwargs
        return (
            f"{self.endpoint_url}/dop-media/photo.jpg"
            "?X-Amz-SignedHeaders=host&X-Amz-Signature=abc"
        )


class MinioConstructorStub:
    calls: list[dict[str, object]] = []

    def __init__(self, endpoint: str, **kwargs: object) -> None:
        self.endpoint = endpoint
        self.kwargs = kwargs
        self.__class__.calls.append({"endpoint": endpoint, **kwargs})


def test_parse_minio_endpoint_url_detects_https() -> None:
    assert media_service.parse_minio_endpoint_url("https://s3.example.com:9443") == (
        "s3.example.com:9443",
        True,
    )


def test_build_minio_client_sets_region(monkeypatch) -> None:
    MinioConstructorStub.calls = []
    monkeypatch.setattr(media_service.settings, "s3_region", "us-east-1")
    monkeypatch.setattr(media_service, "Minio", MinioConstructorStub)

    media_service.build_minio_client("http://127.0.0.1:9000")

    assert MinioConstructorStub.calls[0]["endpoint"] == "127.0.0.1:9000"
    assert MinioConstructorStub.calls[0]["secure"] is False
    assert MinioConstructorStub.calls[0]["region"] == "us-east-1"


def test_get_presigned_put_url_uses_public_presign_endpoint(monkeypatch) -> None:
    clients: list[PresignClientStub] = []

    def build_client(endpoint_url: str) -> PresignClientStub:
        client = PresignClientStub(endpoint_url)
        clients.append(client)
        return client

    monkeypatch.setattr(
        media_service.settings,
        "s3_presigned_url_base",
        "http://127.0.0.1:9000",
    )
    monkeypatch.setattr(media_service, "build_minio_client", build_client)

    result = media_service.get_presigned_put_url("dop-media", "photo.jpg")

    assert result == (
        "http://127.0.0.1:9000/dop-media/photo.jpg"
        "?X-Amz-SignedHeaders=host&X-Amz-Signature=abc"
    )
    assert clients[0].kwargs == {
        "bucket_name": "dop-media",
        "object_name": "photo.jpg",
        "expires": media_service.timedelta(minutes=15),
        "method": "PUT",
    }


def test_get_presigned_put_url_uses_internal_endpoint_without_public_base(monkeypatch) -> None:
    clients: list[PresignClientStub] = []

    def build_client(endpoint_url: str) -> PresignClientStub:
        client = PresignClientStub(endpoint_url)
        clients.append(client)
        return client

    monkeypatch.setattr(media_service.settings, "s3_presigned_url_base", None)
    monkeypatch.setattr(media_service.settings, "s3_endpoint_url", "http://minio:9000")
    monkeypatch.setattr(media_service, "build_minio_client", build_client)

    result = media_service.get_presigned_put_url("dop-media", "photo.jpg")

    assert result.startswith("http://minio:9000/dop-media/photo.jpg")


def test_validate_uploaded_media_object_accepts_expected_file(monkeypatch) -> None:
    monkeypatch.setattr(
        media_service.minio_client,
        "stat_object",
        lambda *_: StatObjectStub(size=1024, content_type="image/jpeg"),
    )

    media_service.validate_uploaded_media_object(
        storage_key="events/event-id/photo.jpg",
        expected_content_type="image/jpeg",
        allowed_content_types={"image/jpeg"},
        max_size_bytes=2048,
    )


def test_validate_uploaded_media_object_rejects_missing_object(monkeypatch) -> None:
    def raise_missing_object(*_: object) -> StatObjectStub:
        raise S3Error(
            code="NoSuchKey",
            message="missing",
            resource="events/event-id/photo.jpg",
            request_id="request-id",
            host_id="host-id",
            response=None,
        )

    monkeypatch.setattr(media_service.minio_client, "stat_object", raise_missing_object)

    with pytest.raises(ValueError, match="Uploaded media object not found"):
        media_service.validate_uploaded_media_object(
            storage_key="events/event-id/photo.jpg",
            expected_content_type="image/jpeg",
            allowed_content_types={"image/jpeg"},
            max_size_bytes=2048,
        )


def test_validate_uploaded_media_object_rejects_empty_file(monkeypatch) -> None:
    monkeypatch.setattr(
        media_service.minio_client,
        "stat_object",
        lambda *_: StatObjectStub(size=0, content_type="image/jpeg"),
    )

    with pytest.raises(ValueError, match="Uploaded media object is empty"):
        media_service.validate_uploaded_media_object(
            storage_key="events/event-id/photo.jpg",
            expected_content_type="image/jpeg",
            allowed_content_types={"image/jpeg"},
            max_size_bytes=2048,
        )


def test_validate_uploaded_media_object_rejects_oversized_file(monkeypatch) -> None:
    monkeypatch.setattr(
        media_service.minio_client,
        "stat_object",
        lambda *_: StatObjectStub(size=4096, content_type="image/jpeg"),
    )

    with pytest.raises(ValueError, match="Uploaded media object is too large"):
        media_service.validate_uploaded_media_object(
            storage_key="events/event-id/photo.jpg",
            expected_content_type="image/jpeg",
            allowed_content_types={"image/jpeg"},
            max_size_bytes=2048,
        )


def test_validate_uploaded_media_object_rejects_content_type_spoofing(monkeypatch) -> None:
    monkeypatch.setattr(
        media_service.minio_client,
        "stat_object",
        lambda *_: StatObjectStub(size=1024, content_type="text/html"),
    )

    with pytest.raises(ValueError, match="Uploaded media content type does not match request"):
        media_service.validate_uploaded_media_object(
            storage_key="events/event-id/photo.jpg",
            expected_content_type="image/jpeg",
            allowed_content_types={"image/jpeg"},
            max_size_bytes=2048,
        )


def test_validate_uploaded_media_object_rejects_disallowed_requested_type(monkeypatch) -> None:
    monkeypatch.setattr(
        media_service.minio_client,
        "stat_object",
        lambda *_: StatObjectStub(size=1024, content_type="image/svg+xml"),
    )

    with pytest.raises(ValueError, match="Uploaded media content type is not allowed"):
        media_service.validate_uploaded_media_object(
            storage_key="events/event-id/image.svg",
            expected_content_type="image/svg+xml",
            allowed_content_types={"image/jpeg"},
            max_size_bytes=2048,
        )
