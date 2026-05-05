from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Employee, MediaFile, MediaKind


async def attach_employee_photo(
    session: AsyncSession,
    employee: Employee,
    storage_key: str,
    public_url: str,
    mime_type: str,
) -> tuple[Employee, MediaFile]:
    photo = MediaFile(
        storage_key=storage_key,
        public_url=public_url,
        mime_type=mime_type,
        kind=MediaKind.image,
    )

    session.add(photo)
    await session.flush()
    employee.photo_id = photo.id
    await session.commit()
    await session.refresh(employee)
    await session.refresh(photo)
    return employee, photo
