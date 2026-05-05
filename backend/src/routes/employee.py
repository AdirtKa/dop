"""HTTP-маршруты для работы со списком сотрудников."""

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.logger import get_error_logger
from src.models import Employee, User
from src.repository.employee import add_employee, get_employees
from src.repository.media import attach_employee_photo
from src.routes.auth.dependency import require_admin
from src.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdateResponse
from src.services.media import get_presigned_put_url
from src.session import get_session

router = APIRouter()
SessionDependency = Annotated[AsyncSession, Depends(get_session)]
error_logger = get_error_logger()

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


@router.get("/", response_model=list[EmployeeRead])
async def read_employees(session: SessionDependency):
    """Возвращает список сотрудников для клиентского каталога."""
    try:
        employees = await get_employees(session)
        return employees
    except HTTPException:
        raise
    except Exception as exc:
        error_logger.exception("Failed to load employees list", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load employees",
        ) from exc


@router.post("/", response_model=EmployeeUpdateResponse)
async def create_employee(
    session: SessionDependency,
    employee_data: EmployeeCreate,
    current_user: Annotated[User, Depends(require_admin)],  # noqa ARG001
):
    """Создает сотрудника в базе данных и возвращает его."""

    try:
        if employee_data.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Недопустимый тип файла",
            )
        ext: str = employee_data.photo_filename.split(".")[-1]
        storage_key: str = f"employees/{uuid.uuid4()}.{ext}"
        presigned_url: str = get_presigned_put_url(settings.s3_bucket_name, storage_key)
        public_url: str = f"{settings.s3_public_url}/{storage_key}"

        employee: Employee = await add_employee(session, employee_data)
        employee, photo = await attach_employee_photo(
            session, employee, storage_key, public_url, employee_data.content_type
        )
        return EmployeeUpdateResponse(
            id=employee.id,
            full_name=employee.full_name,
            position=employee.position,
            experience=employee.experience,
            photo=photo,
            presigned_url=presigned_url,
        )

    except HTTPException:
        raise

    except Exception as exc:
        error_logger.exception("Failed to create employee", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create employee",
        ) from exc
