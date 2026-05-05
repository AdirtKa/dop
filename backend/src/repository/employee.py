"""Репозиторий для чтения сотрудников."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.employee import Employee
from src.schemas import EmployeeCreate


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


async def add_employee(
    session: AsyncSession,
    employee: EmployeeCreate,
) -> Employee:
    employee = Employee(
        full_name=employee.full_name,
        position=employee.position,
        experience=employee.experience,
    )
    session.add(employee)
    await session.commit()
    await session.refresh(employee)
    return employee
