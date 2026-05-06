from __future__ import annotations

from datetime import UTC, datetime
import uuid

import pytest

from src.schemas import (
    EmployeeCreateRequest,
    EmployeePatchRequest,
    EmployeePhotoUpdateRequest,
    EmployeePutResponse,
    MediaFileRead,
)


def test_employee_create_request_accepts_expected_payload() -> None:
    payload = EmployeeCreateRequest(
        full_name="Alice Example",
        position="Engineer",
        experience="5 years",
        photo_filename="alice.png",
        content_type="image/png",
    )

    assert payload.full_name == "Alice Example"
    assert payload.photo_filename == "alice.png"


def test_employee_create_request_allows_missing_photo_fields() -> None:
    payload = EmployeeCreateRequest(
        full_name="Alice Example",
        position="Engineer",
        experience="5 years",
    )

    assert payload.photo_filename is None
    assert payload.content_type is None


def test_employee_create_request_rejects_partial_photo_metadata() -> None:
    with pytest.raises(
        ValueError, match="photo_filename and content_type must be provided together"
    ):
        EmployeeCreateRequest(
            full_name="Alice Example",
            position="Engineer",
            experience="5 years",
            photo_filename="alice.png",
        )


def test_employee_patch_request_exposes_updated_fields() -> None:
    payload = EmployeePatchRequest(
        full_name="Alice Updated",
        position="Lead Engineer",
        experience="6 years",
    )

    assert payload.model_dump() == {
        "full_name": "Alice Updated",
        "position": "Lead Engineer",
        "experience": "6 years",
    }


def test_employee_photo_update_request_keeps_file_metadata() -> None:
    payload = EmployeePhotoUpdateRequest(
        photo_filename="alice.webp",
        content_type="image/webp",
    )

    assert payload.photo_filename == "alice.webp"
    assert payload.content_type == "image/webp"


def test_employee_put_response_supports_optional_experience_and_photo() -> None:
    photo = MediaFileRead(
        id=uuid.uuid4(),
        public_url="https://cdn.example.com/employees/alice.png",
        mime_type="image/png",
        kind="image",
        created_at=datetime.now(UTC),
    )
    payload = EmployeePutResponse(
        id=uuid.uuid4(),
        full_name="Alice Example",
        position="Engineer",
        experience=None,
        photo=photo,
        presigned_url="https://s3.example.com/presigned",
    )

    assert payload.experience is None
    assert payload.photo == photo


def test_employee_put_response_allows_missing_presigned_url() -> None:
    payload = EmployeePutResponse(
        id=uuid.uuid4(),
        full_name="Alice Example",
        position="Engineer",
        experience="5 years",
        photo=None,
        presigned_url=None,
    )

    assert payload.presigned_url is None
