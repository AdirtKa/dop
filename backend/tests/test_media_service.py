from __future__ import annotations

from dataclasses import dataclass

from minio.error import S3Error
import pytest

from src.services import media as media_service


@dataclass
class StatObjectStub:
    size: int | None
    content_type: str | None


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
