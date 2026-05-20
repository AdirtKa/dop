"""Репозиторий для чтения сотрудников."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import MediaFile
from src.models.employee import Employee
from src.schemas import EmployeeCreateRequest, EmployeePatchRequest


async def get_employees(
    session: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> list[Employee]:
    """Возвращает список сотрудников с подгруженной фотографией."""
    stmt = (
        select(Employee)
        .options(selectinload(Employee.photo))
        .order_by(Employee.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await session.execute(stmt)

    return list(result.scalars().all())


async def get_employee_by_id(
    session: AsyncSession,
    employee_id: uuid.UUID,
) -> Employee | None:
    """Возвращает сотрудника по идентификатору вместе с фотографией."""
    stmt = select(Employee).options(selectinload(Employee.photo)).where(Employee.id == employee_id)

    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def add_employee(
    session: AsyncSession,
    employee_data: EmployeeCreateRequest,
) -> Employee:
    """Создает сотрудника на основе входной схемы и сохраняет его в БД."""
    employee = Employee(
        full_name=employee_data.full_name,
        position=employee_data.position,
        experience=employee_data.experience,
    )
    session.add(employee)
    await session.commit()
    await session.refresh(employee)
    return employee


async def patch_employee(
    session: AsyncSession,
    employee_id: uuid.UUID,
    data: EmployeePatchRequest,
) -> Employee | None:
    """Обновляет измененные поля сотрудника и возвращает актуальную модель."""
    stmt = select(Employee).where(Employee.id == employee_id).options(selectinload(Employee.photo))
    result = await session.execute(stmt)
    employee = result.scalars().first()

    if employee is None:
        return None

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(employee, field, value)

    await session.commit()
    await session.refresh(employee)

    return employee


async def update_employee_photo_data(
    session: AsyncSession,
    employee: Employee,
    content_type: str,
) -> MediaFile:
    """Обновляет MIME-тип уже привязанной фотографии сотрудника."""
    if employee.photo is None:
        raise ValueError("Employee photo not found")

    employee.photo.mime_type = content_type

    await session.commit()
    await session.refresh(employee.photo)

    return employee.photo


async def delete_employee_by_id(
    session: AsyncSession,
    employee_id: uuid.UUID,
) -> bool:
    """Удаляет сотрудника по идентификатору и сообщает, был ли он найден."""
    employee = await session.get(Employee, employee_id)

    if employee is None:
        return False

    await session.delete(employee)
    await session.commit()

    return True
