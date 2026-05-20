from __future__ import annotations

from datetime import UTC, datetime
import uuid

import pytest

from src.models import EventHall
from src.schemas.event import (
    EventCreateRequest,
    EventPatchRequest,
    ExtendedReadEventResponse,
    ReadEventResponse,
    OrganizationShortRead,
)


def test_event_create_request_defaults_to_large_hall() -> None:
    payload = EventCreateRequest(
        name="Conference",
        start_time=datetime(2026, 5, 10, 10, 0, tzinfo=UTC),
        end_time=datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
    )

    assert payload.halls == [EventHall.large]
    assert payload.details == ""
    assert payload.representative == ""
    assert payload.responsible_name == ""
    assert payload.responsible_contact == ""


def test_event_patch_request_accepts_known_halls() -> None:
    payload = EventPatchRequest(
        name="Conference",
        details="Updated details",
        representative="Organizer representative",
        responsible_name="Responsible Person",
        responsible_contact="+7 999 000-00-00",
        halls=["buffet", "large"],
        start_time=datetime(2026, 5, 10, 10, 0, tzinfo=UTC),
        end_time=datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
        is_public=True,
        organization_id=None,
    )

    assert payload.halls == [EventHall.buffet, EventHall.large]


def test_event_patch_request_rejects_unknown_hall() -> None:
    with pytest.raises(ValueError):
        EventPatchRequest(
            name="Conference",
            details="Updated details",
            representative="Organizer representative",
            responsible_name="Responsible Person",
            responsible_contact="+7 999 000-00-00",
            halls=["roof"],
            start_time=datetime(2026, 5, 10, 10, 0, tzinfo=UTC),
            end_time=datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
            is_public=True,
            organization_id=None,
        )


def test_event_patch_request_rejects_empty_halls() -> None:
    with pytest.raises(ValueError):
        EventPatchRequest(
            name="Conference",
            details="Updated details",
            representative="Organizer representative",
            responsible_name="Responsible Person",
            responsible_contact="+7 999 000-00-00",
            halls=[],
            start_time=datetime(2026, 5, 10, 10, 0, tzinfo=UTC),
            end_time=datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
            is_public=True,
            organization_id=None,
        )


def test_read_event_response_excludes_internal_visibility_fields() -> None:
    payload = ReadEventResponse(
        id=uuid.uuid4(),
        name="Conference",
        representative="Organizer representative",
        responsible_name="Responsible Person",
        responsible_contact="+7 999 000-00-00",
        halls=[EventHall.small],
        start_time=datetime(2026, 5, 10, 10, 0, tzinfo=UTC),
        end_time=datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
        organization=None,
        media=[],
    )

    dumped = payload.model_dump()

    assert dumped["halls"] == [EventHall.small]
    assert "details" not in dumped
    assert "is_public" not in dumped


def test_extended_read_event_response_contains_internal_visibility_fields() -> None:
    payload = ExtendedReadEventResponse(
        id=uuid.uuid4(),
        name="Conference",
        representative="Organizer representative",
        responsible_name="Responsible Person",
        responsible_contact="+7 999 000-00-00",
        halls=[EventHall.buffet, EventHall.large],
        start_time=datetime(2026, 5, 10, 10, 0, tzinfo=UTC),
        end_time=datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
        organization=OrganizationShortRead.model_validate(
            {"id": uuid.uuid4(), "full_name": "Organizer"}
        ),
        media=[],
        details="Internal details",
        is_public=False,
    )

    assert payload.details == "Internal details"
    assert payload.is_public is False
    assert payload.halls == [EventHall.buffet, EventHall.large]
