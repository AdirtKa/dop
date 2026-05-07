from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Employee, Event, MediaFile
from src.models.media_file import MediaKind


async def create_media_file(
    session: AsyncSession,
    storage_key: str,
    public_url: str,
    mime_type: str,
    media_kind: MediaKind,
) -> MediaFile:
    """Создаёт MediaFile и делает flush, но не commit."""

    media_file = MediaFile(
        storage_key=storage_key,
        public_url=public_url,
        mime_type=mime_type,
        kind=media_kind,
    )

    session.add(media_file)
    await session.flush()

    return media_file


async def attach_employee_photo(
    session: AsyncSession,
    employee: Employee,
    storage_key: str,
    public_url: str,
    mime_type: str,
) -> tuple[Employee, MediaFile]:
    """Создаёт фото и привязывает его к сотруднику."""

    photo = await create_media_file(
        session=session,
        storage_key=storage_key,
        public_url=public_url,
        mime_type=mime_type,
        media_kind=MediaKind.image,
    )

    employee.photo_id = photo.id

    await session.commit()
    await session.refresh(employee)
    await session.refresh(photo)

    return employee, photo


async def attach_event_media(
    session: AsyncSession,
    event: Event,
    storage_key: str,
    public_url: str,
    mime_type: str,
    media_kind: MediaKind,
) -> tuple[Event, MediaFile]:
    """Создаёт медиафайл и привязывает его к мероприятию."""

    media = await create_media_file(
        session=session,
        storage_key=storage_key,
        public_url=public_url,
        mime_type=mime_type,
        media_kind=media_kind,
    )

    await session.refresh(event, attribute_names=["media"])
    event.media.append(media)

    await session.commit()
    await session.refresh(event)
    await session.refresh(media)

    return event, media
