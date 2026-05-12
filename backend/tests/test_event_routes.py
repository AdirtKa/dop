from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
import uuid

from fastapi import HTTPException
import pytest

from src.models import Event, MediaFile, MediaKind, MediaStatus, User, UserRole
from src.routes import event as event_routes
from src.schemas.event import EventCreateRequest, EventMediaCreateRequest, EventMediaUpdateRequest


def make_event(*, organization_id: uuid.UUID | None = None) -> Event:
    event = Event(
        name="Conference",
        start_time=datetime(2026, 5, 10, 10, 0, tzinfo=UTC),
        end_time=datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
        is_public=False,
        organization_id=organization_id,
    )
    event.id = uuid.uuid4()
    event.organization = None
    return event


def make_media(*, status: MediaStatus = MediaStatus.pending) -> MediaFile:
    media = MediaFile(
        storage_key="events/event-id/media.jpg",
        public_url=None,
        mime_type="image/jpeg",
        kind=MediaKind.image,
        status=status,
    )
    media.id = uuid.uuid4()
    media.created_at = datetime.now(UTC)
    return media


@pytest.mark.asyncio
async def test_create_event_registers_media_as_pending_without_public_url(monkeypatch) -> None:
    event = make_event()
    media = make_media()
    attach_mock = AsyncMock(return_value=(event, media))

    monkeypatch.setattr(event_routes, "add_event", AsyncMock(return_value=event))
    monkeypatch.setattr(event_routes, "attach_event_media", attach_mock)
    monkeypatch.setattr(
        event_routes,
        "build_media_payload",
        lambda **_: (
            "events/event-id/media.jpg",
            "https://s3.example.com/presigned",
            "https://cdn.example.com/events/event-id/media.jpg",
        ),
    )

    result = await event_routes.create_event(
        session=object(),
        event_data=EventCreateRequest(
            name="Conference",
            start_time=event.start_time,
            end_time=event.end_time,
            is_public=False,
            media=[{"filename": "media.jpg", "content_type": "image/jpeg"}],
        ),
        current_user=User(
            id=uuid.uuid4(),
            username="admin",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        ),
    )

    assert result.upload_urls[0].presigned_url == "https://s3.example.com/presigned"
    assert result.media[0].public_url is None
    assert result.media[0].status == MediaStatus.pending
    attach_mock.assert_awaited_once()
    assert attach_mock.await_args.kwargs["public_url"] is None


@pytest.mark.asyncio
async def test_complete_event_media_upload_marks_media_ready(monkeypatch) -> None:
    media = make_media(status=MediaStatus.pending)
    ready_media = make_media(status=MediaStatus.ready)
    ready_media.id = media.id
    ready_media.public_url = "https://cdn.example.com/events/event-id/media.jpg"

    monkeypatch.setattr(event_routes, "get_event_media", AsyncMock(return_value=media))
    monkeypatch.setattr(event_routes, "validate_uploaded_media_object", lambda **_: None)
    monkeypatch.setattr(
        event_routes,
        "mark_event_media_ready",
        AsyncMock(return_value=ready_media),
    )
    failed_mock = AsyncMock()
    monkeypatch.setattr(event_routes, "mark_event_media_failed", failed_mock)

    result = await event_routes.complete_event_media_upload(
        session=object(),
        event_id=uuid.uuid4(),
        media_id=media.id,
        current_user=User(
            id=uuid.uuid4(),
            username="admin",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        ),
    )

    assert result.status == MediaStatus.ready
    assert result.public_url == ready_media.public_url
    failed_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_event_media_upload_returns_pending_media(monkeypatch) -> None:
    event = make_event()
    media = make_media(status=MediaStatus.pending)

    monkeypatch.setattr(event_routes, "get_event_owner", AsyncMock(return_value=None))
    monkeypatch.setattr(event_routes, "get_event_by_id", AsyncMock(return_value=event))
    monkeypatch.setattr(
        event_routes,
        "build_media_payload",
        lambda **_: (
            "events/event-id/new.jpg",
            "https://s3.example.com/new-presigned",
            "https://cdn.example.com/events/event-id/new.jpg",
        ),
    )
    attach_mock = AsyncMock(return_value=(event, media))
    monkeypatch.setattr(event_routes, "attach_event_media", attach_mock)

    result = await event_routes.add_event_media_upload(
        session=object(),
        event_id=event.id,
        media_data=EventMediaCreateRequest(filename="new.jpg", content_type="image/jpeg"),
        current_user=User(
            id=uuid.uuid4(),
            username="admin",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        ),
    )

    assert result.presigned_url == "https://s3.example.com/new-presigned"
    assert result.media_file.status == MediaStatus.pending
    assert result.media_file.public_url is None
    attach_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_event_media_upload_reissues_presigned_url(monkeypatch) -> None:
    media = make_media(status=MediaStatus.ready)
    updated_media = make_media(status=MediaStatus.pending)
    updated_media.id = media.id
    updated_media.storage_key = media.storage_key

    monkeypatch.setattr(event_routes, "get_event_owner", AsyncMock(return_value=None))
    monkeypatch.setattr(event_routes, "get_event_media", AsyncMock(return_value=media))
    update_mock = AsyncMock(return_value=updated_media)
    monkeypatch.setattr(event_routes, "update_event_media_upload_data", update_mock)
    monkeypatch.setattr(
        event_routes,
        "get_presigned_put_url",
        lambda *_: "https://s3.example.com/reupload",
    )

    result = await event_routes.update_event_media_upload(
        session=object(),
        event_id=uuid.uuid4(),
        media_id=media.id,
        media_data=EventMediaUpdateRequest(filename="replace.jpg", content_type="image/jpeg"),
        current_user=User(
            id=uuid.uuid4(),
            username="admin",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
        ),
    )

    assert result.presigned_url == "https://s3.example.com/reupload"
    assert result.media_file.status == MediaStatus.pending
    assert result.media_file.public_url is None
    update_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_complete_event_media_upload_marks_media_failed_on_invalid_object(
    monkeypatch,
) -> None:
    media = make_media(status=MediaStatus.pending)
    failed_mock = AsyncMock()

    monkeypatch.setattr(event_routes, "get_event_media", AsyncMock(return_value=media))
    monkeypatch.setattr(
        event_routes,
        "validate_uploaded_media_object",
        lambda **_: (_ for _ in ()).throw(ValueError("Uploaded media object is too large")),
    )
    monkeypatch.setattr(event_routes, "mark_event_media_failed", failed_mock)
    session = object()

    with pytest.raises(HTTPException) as exc:
        await event_routes.complete_event_media_upload(
            session=session,
            event_id=uuid.uuid4(),
            media_id=media.id,
            current_user=User(
                id=uuid.uuid4(),
                username="admin",
                password_hash="hash",
                role=UserRole.ADMIN,
                is_active=True,
            ),
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Uploaded media object is too large"
    failed_mock.assert_awaited_once_with(session, media)
