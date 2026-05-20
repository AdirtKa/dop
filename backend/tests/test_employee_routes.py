from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
import uuid

from fastapi import HTTPException
import pytest

from src.models import Employee, MediaFile, MediaKind
from src.routes import employee as employee_routes
from src.schemas.employee import EmployeeCreateRequest, EmployeePhotoUpdateRequest


def make_employee(*, with_photo: bool = False) -> Employee:
    employee = Employee(
        full_name="Alice Example",
        position="Engineer",
        experience="5 years",
    )
    employee.id = uuid.uuid4()
    if with_photo:
        photo = MediaFile(
            storage_key="employees/existing.png",
            public_url="https://cdn.example.com/employees/existing.png",
            mime_type="image/png",
            kind=MediaKind.image,
        )
        photo.id = uuid.uuid4()
        photo.created_at = datetime.now(UTC)
        employee.photo = photo
    else:
        employee.photo = None
    return employee


@pytest.mark.asyncio
async def test_create_employee_allows_missing_photo(monkeypatch) -> None:
    employee = make_employee()
    session = object()

    monkeypatch.setattr(
        employee_routes,
        "add_employee",
        AsyncMock(return_value=employee),
    )
    attach_mock = AsyncMock()
    monkeypatch.setattr(employee_routes, "attach_employee_photo", attach_mock)

    result = await employee_routes.create_employee(
        session=session,
        employee_data=EmployeeCreateRequest(
            full_name="Alice Example",
            position="Engineer",
            experience="5 years",
        ),
        _=object(),
    )

    assert result.id == employee.id
    assert result.photo is None
    assert result.presigned_url is None
    attach_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_employee_with_photo_keeps_existing_flow(monkeypatch) -> None:
    employee = make_employee()
    photo = MediaFile(
        storage_key="employees/new.png",
        public_url="https://cdn.example.com/employees/new.png",
        mime_type="image/png",
        kind=MediaKind.image,
    )
    photo.id = uuid.uuid4()
    photo.created_at = datetime.now(UTC)

    monkeypatch.setattr(
        employee_routes,
        "add_employee",
        AsyncMock(return_value=employee),
    )
    monkeypatch.setattr(
        employee_routes,
        "attach_employee_photo",
        AsyncMock(return_value=(employee, photo)),
    )
    monkeypatch.setattr(
        employee_routes,
        "build_media_payload",
        lambda **_: (
            "employees/generated.png",
            "https://s3.example.com/presigned",
            "https://cdn.example.com/employees/generated.png",
        ),
    )

    result = await employee_routes.create_employee(
        session=object(),
        employee_data=EmployeeCreateRequest(
            full_name="Alice Example",
            position="Engineer",
            experience="5 years",
            photo_filename="alice.png",
            content_type="image/png",
        ),
        _=object(),
    )

    assert result.photo is not None
    assert result.photo.mime_type == "image/png"
    assert result.presigned_url == "https://s3.example.com/presigned"


@pytest.mark.asyncio
async def test_update_employee_photo_attaches_photo_when_missing(monkeypatch) -> None:
    employee = make_employee(with_photo=False)
    photo = MediaFile(
        storage_key="employees/new.webp",
        public_url="https://cdn.example.com/employees/new.webp",
        mime_type="image/webp",
        kind=MediaKind.image,
    )
    photo.id = uuid.uuid4()
    photo.created_at = datetime.now(UTC)

    monkeypatch.setattr(
        employee_routes,
        "get_employee_by_id",
        AsyncMock(return_value=employee),
    )
    monkeypatch.setattr(
        employee_routes,
        "attach_employee_photo",
        AsyncMock(return_value=(employee, photo)),
    )
    monkeypatch.setattr(
        employee_routes,
        "build_media_payload",
        lambda **_: (
            "employees/generated.webp",
            "https://s3.example.com/presigned-photo",
            "https://cdn.example.com/employees/generated.webp",
        ),
    )

    result = await employee_routes.update_employee_photo(
        session=object(),
        employee_id=employee.id,
        employee_data=EmployeePhotoUpdateRequest(
            photo_filename="alice.webp",
            content_type="image/webp",
        ),
        _=object(),
    )

    assert result.photo is not None
    assert result.photo.mime_type == "image/webp"
    assert result.presigned_url == "https://s3.example.com/presigned-photo"


@pytest.mark.asyncio
async def test_update_employee_photo_rejects_unsupported_type(monkeypatch) -> None:
    monkeypatch.setattr(
        employee_routes,
        "get_employee_by_id",
        AsyncMock(),
    )

    with pytest.raises(HTTPException) as exc:
        await employee_routes.update_employee_photo(
            session=object(),
            employee_id=uuid.uuid4(),
            employee_data=EmployeePhotoUpdateRequest(
                photo_filename="alice.gif",
                content_type="image/gif",
            ),
            _=object(),
        )

    assert exc.value.status_code == 400
