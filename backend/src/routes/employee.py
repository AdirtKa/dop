"""HTTP-маршруты для работы со списком сотрудников."""

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from src.config import settings
from src.logger import get_error_logger
from src.models import Employee, User
from src.repository.employee import (
    add_employee,
    delete_employee_by_id,
    get_employee_by_id,
    get_employees,
    patch_employee,
    update_employee_photo_data,
)
from src.repository.media import attach_employee_photo
from src.routes.auth.auth import session_dependency
from src.routes.auth.dependency import require_admin
from src.schemas import MediaFileRead
from src.schemas.employee import (
    EmployeeCreateRequest,
    EmployeePatchRequest,
    EmployeePhotoUpdateRequest,
    EmployeePutResponse,
    EmployeeRead,
)
from src.services.media import build_media_payload, get_presigned_put_url

router = APIRouter()
error_logger = get_error_logger()

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

STORAGE_PREFIX: str = "employees"


@router.get("/", response_model=list[EmployeeRead])
async def read_employees(session: session_dependency):
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


@router.post("/", response_model=EmployeePutResponse)
async def create_employee(
    session: session_dependency,
    employee_data: EmployeeCreateRequest,
    _: Annotated[User, Depends(require_admin)],
):
    """Создает сотрудника в базе данных и возвращает его."""

    try:
        if (
            employee_data.content_type is not None
            and employee_data.content_type not in ALLOWED_IMAGE_TYPES
        ):
            raise HTTPException(
                status_code=400,
                detail="Недопустимый тип файла",
            )

        employee: Employee = await add_employee(session, employee_data)
        photo: MediaFileRead | None = None
        presigned_url: str | None = None

        if employee_data.photo_filename is not None and employee_data.content_type is not None:
            storage_key, presigned_url, public_url = build_media_payload(
                filename=employee_data.photo_filename,
                storage_prefix=STORAGE_PREFIX,
            )
            employee, attached_photo = await attach_employee_photo(
                session,
                employee,
                storage_key,
                public_url,
                employee_data.content_type,
            )
            photo = MediaFileRead.model_validate(attached_photo)

        return EmployeePutResponse(
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


@router.patch("/{employee_id}", response_model=EmployeeRead)
async def update_employee(
    session: session_dependency,
    employee_id: uuid.UUID,
    employee_data: EmployeePatchRequest,
    _: Annotated[User, Depends(require_admin)],
):
    """Обновляет текстовые поля сотрудника по идентификатору."""
    try:
        employee = await patch_employee(session, employee_id, employee_data)
        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to update employee",
            )
        return employee

    except HTTPException:
        raise
    except Exception as exc:
        error_logger.exception("Failed to update employee", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update employee",
        ) from exc


@router.put("/{employee_id}/photo", response_model=EmployeePutResponse)
async def update_employee_photo(
    session: session_dependency,
    employee_id: uuid.UUID,
    employee_data: EmployeePhotoUpdateRequest,
    _: Annotated[User, Depends(require_admin)],
):
    """Готовит обновление фотографии сотрудника и возвращает URL загрузки."""
    try:
        if employee_data.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Недопустимый тип файла",
            )
        employee = await get_employee_by_id(session, employee_id)
        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to update employee",
            )

        if employee.photo is None:
            storage_key, presigned_url, public_url = build_media_payload(
                filename=employee_data.photo_filename,
                storage_prefix=STORAGE_PREFIX,
            )
            employee, photo = await attach_employee_photo(
                session,
                employee,
                storage_key,
                public_url,
                employee_data.content_type,
            )
        else:
            photo = await update_employee_photo_data(session, employee, employee_data.content_type)
            presigned_url = get_presigned_put_url(
                settings.s3_bucket_name, employee.photo.storage_key
            )

        photo = MediaFileRead.model_validate(photo)
        return EmployeePutResponse(
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
        error_logger.exception("Failed to update employee photo", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update employee photo",
        ) from exc


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    session: session_dependency,
    employee_id: uuid.UUID,
) -> None:
    """Удаляет сотрудника по идентификатору."""
    deleted = await delete_employee_by_id(session, employee_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )
