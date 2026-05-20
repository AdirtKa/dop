from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
import uuid

import pytest

from src.models import Employee, MediaFile, MediaKind
from src.repository import employee as employee_repository
from src.schemas import EmployeeCreateRequest, EmployeePatchRequest


class ExecuteResultStub:
    def __init__(self, employee: Employee) -> None:
        self.employee = employee

    def scalar_one_or_none(self) -> Employee:
        return self.employee

    def scalars(self) -> ExecuteScalarsStub:
        return ExecuteScalarsStub(self.employee)


class ExecuteScalarsStub:
    def __init__(self, employee: Employee | None) -> None:
        self.employee = employee

    def first(self) -> Employee | None:
        return self.employee


class AddSessionStub:
    def __init__(self, added: list[Employee]) -> None:
        self._added = added
        self.commit = AsyncMock()
        self.refresh = AsyncMock()

    def add(self, obj: Employee) -> None:
        self._added.append(obj)


@pytest.mark.asyncio
async def test_get_employee_by_id_returns_employee_from_scalar_result() -> None:
    employee = Employee(full_name="Alice Example", position="Engineer", experience="5 years")
    expected_id = uuid.uuid4()
    employee.id = expected_id
    execute_result = ExecuteResultStub(employee)
    session = type("Session", (), {"execute": AsyncMock(return_value=execute_result)})()

    result = await employee_repository.get_employee_by_id(session, expected_id)

    assert result is employee
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_employee_persists_new_employee() -> None:
    added: list[Employee] = []
    session = AddSessionStub(added)
    payload = EmployeeCreateRequest(
        full_name="Alice Example",
        position="Engineer",
        experience="5 years",
        photo_filename="alice.png",
        content_type="image/png",
    )

    result = await employee_repository.add_employee(session, payload)

    assert result is added[0]
    assert result.full_name == payload.full_name
    assert result.position == payload.position
    assert result.experience == payload.experience
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_patch_employee_updates_all_fields_and_refreshes_entity() -> None:
    employee = Employee(full_name="Alice Example", position="Engineer", experience="5 years")
    session = type(
        "Session",
        (),
        {
            "execute": AsyncMock(return_value=ExecuteResultStub(employee)),
            "commit": AsyncMock(),
            "refresh": AsyncMock(),
        },
    )()
    payload = EmployeePatchRequest(
        full_name="Alice Updated",
        position="Lead Engineer",
        experience="6 years",
    )

    result = await employee_repository.patch_employee(session, uuid.uuid4(), payload)

    assert result is employee
    assert employee.full_name == payload.full_name
    assert employee.position == payload.position
    assert employee.experience == payload.experience
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(employee)


@pytest.mark.asyncio
async def test_patch_employee_returns_none_when_employee_is_missing() -> None:
    session = type(
        "Session",
        (),
        {
            "execute": AsyncMock(return_value=ExecuteResultStub(None)),
            "commit": AsyncMock(),
            "refresh": AsyncMock(),
        },
    )()
    payload = EmployeePatchRequest(
        full_name="Alice Updated",
        position="Lead Engineer",
        experience="6 years",
    )

    result = await employee_repository.patch_employee(session, uuid.uuid4(), payload)

    assert result is None
    session.commit.assert_not_awaited()
    session.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_employee_photo_data_updates_mime_type() -> None:
    photo = MediaFile(
        storage_key="employees/photo.png",
        public_url="https://cdn.example.com/employees/photo.png",
        mime_type="image/png",
        kind=MediaKind.image,
    )
    photo.id = uuid.uuid4()
    photo.created_at = datetime.now(UTC)
    employee = Employee(full_name="Alice Example", position="Engineer", experience="5 years")
    employee.photo = photo
    session = type(
        "Session",
        (),
        {
            "commit": AsyncMock(),
            "refresh": AsyncMock(),
        },
    )()

    result = await employee_repository.update_employee_photo_data(
        session,
        employee,
        "image/webp",
    )

    assert result is photo
    assert photo.mime_type == "image/webp"
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(photo)


@pytest.mark.asyncio
async def test_update_employee_photo_data_raises_when_photo_is_missing() -> None:
    employee = Employee(full_name="Alice Example", position="Engineer", experience="5 years")
    employee.photo = None
    session = type(
        "Session",
        (),
        {
            "commit": AsyncMock(),
            "refresh": AsyncMock(),
        },
    )()

    with pytest.raises(ValueError, match="Employee photo not found"):
        await employee_repository.update_employee_photo_data(
            session,
            employee,
            "image/webp",
        )

    session.commit.assert_not_awaited()
    session.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_employee_by_id_deletes_existing_employee() -> None:
    employee = Employee(full_name="Alice Example", position="Engineer", experience="5 years")
    session = type(
        "Session",
        (),
        {
            "get": AsyncMock(return_value=employee),
            "delete": AsyncMock(),
            "commit": AsyncMock(),
        },
    )()

    result = await employee_repository.delete_employee_by_id(session, uuid.uuid4())

    assert result is True
    session.delete.assert_awaited_once_with(employee)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_employee_by_id_returns_false_for_unknown_employee() -> None:
    session = type(
        "Session",
        (),
        {
            "get": AsyncMock(return_value=None),
            "delete": AsyncMock(),
            "commit": AsyncMock(),
        },
    )()

    result = await employee_repository.delete_employee_by_id(session, uuid.uuid4())

    assert result is False
    session.delete.assert_not_awaited()
    session.commit.assert_not_awaited()
