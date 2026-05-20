from datetime import UTC, datetime, timedelta
import uuid
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import settings
from src.models import Event, MediaFile, MediaKind, MediaStatus, event_media
from src.schemas import EventCreateRequest, EventPatchRequest


async def get_events(
    session: AsyncSession,
    limit: int = 10,
    offset: int = 0,
    is_public: bool | None = None,
    is_finished: bool | None = None,
    organization_id: UUID | None = None,
    include_own_events: bool = False,
) -> list[Event]:
    days_delay = 1

    stmt = (
        select(Event)
        .options(selectinload(Event.media))
        .options(selectinload(Event.organization))
        .order_by(Event.start_time.desc())
    )

    conditions = []

    if is_public is not None:
        conditions.append(Event.is_public.is_(is_public))

    if is_finished is not None:
        border_time = datetime.now(UTC) - timedelta(days=days_delay)

        if is_finished:
            conditions.append(Event.end_time < border_time)
        else:
            conditions.append(Event.end_time >= border_time)

    if include_own_events and organization_id is not None:
        stmt = stmt.where(
            or_(
                and_(*conditions),
                Event.organization_id == organization_id,
            )
        )
    elif conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.limit(limit).offset(offset)

    result = await session.execute(stmt)

    return list(result.scalars().all())


async def add_event(
    session: AsyncSession,
    event_data: EventCreateRequest,
) -> Event:
    event = Event(
        name=event_data.name,
        details=event_data.details,
        representative=event_data.representative,
        responsible_name=event_data.responsible_name,
        responsible_contact=event_data.responsible_contact,
        halls=event_data.halls,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        is_public=event_data.is_public,
        organization_id=event_data.organization_id,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def has_event_time_conflict(
    session: AsyncSession,
    start_time: datetime,
    end_time: datetime,
    organization_id: UUID | None,
    exclude_event_id: UUID | None = None,
) -> bool:
    conditions = [
        Event.start_time < end_time,
        Event.end_time > start_time,
    ]

    if organization_id is not None:
        conditions.append(
            or_(
                Event.organization_id.is_(None),
                Event.organization_id != organization_id,
            )
        )

    if exclude_event_id is not None:
        conditions.append(Event.id != exclude_event_id)

    stmt = select(Event.id).where(and_(*conditions)).limit(1)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_event_by_id(session: AsyncSession, event_id: uuid.UUID) -> Event | None:
    stmt = (
        select(Event)
        .where(Event.id == event_id)
        .options(selectinload(Event.media))
        .options(selectinload(Event.organization))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def delete_event_by_id(session: AsyncSession, event_id: uuid.UUID) -> bool:
    event = await session.get(Event, event_id)
    if event is None:
        return False

    await session.delete(event)
    await session.commit()

    return True


async def patch_event(
    session: AsyncSession,
    event_id: uuid.UUID,
    event_data: EventPatchRequest,
) -> Event | None:
    event = await session.get(Event, event_id)

    if event is None:
        return None

    update_data = event_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(event, field, value)

    await session.commit()

    stmt = (
        select(Event)
        .where(Event.id == event_id)
        .options(selectinload(Event.media))
        .options(selectinload(Event.organization))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def change_visibility(session: AsyncSession, event_id: uuid.UUID, is_public: bool) -> bool:
    event = await session.get(Event, event_id)
    if event is None:
        return False

    event.is_public = is_public
    await session.commit()
    await session.refresh(event)
    return True


async def get_event_owner(session: AsyncSession, event_id: uuid.UUID) -> UUID | None:
    event = await session.get(Event, event_id)
    if event is None:
        return None

    return event.organization_id


async def get_event_media(
    session: AsyncSession,
    event_id: uuid.UUID,
    media_id: uuid.UUID,
) -> MediaFile | None:
    stmt = (
        select(MediaFile)
        .join(event_media, event_media.c.media_file_id == MediaFile.id)
        .where(
            event_media.c.event_id == event_id,
            MediaFile.id == media_id,
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def mark_event_media_ready(session: AsyncSession, media: MediaFile) -> MediaFile:
    media.status = MediaStatus.ready
    media.public_url = f"{settings.s3_public_url}/{media.storage_key}"

    await session.commit()
    await session.refresh(media)

    return media


async def mark_event_media_failed(session: AsyncSession, media: MediaFile) -> None:
    media.status = MediaStatus.failed
    await session.commit()


async def update_event_media_upload_data(
    session: AsyncSession,
    media: MediaFile,
    mime_type: str,
    media_kind: MediaKind,
) -> MediaFile:
    media.mime_type = mime_type
    media.kind = media_kind
    media.status = MediaStatus.pending
    media.public_url = None

    await session.commit()
    await session.refresh(media)

    return media


async def delete_event_media(
    session: AsyncSession,
    event_id: uuid.UUID,
    media_id: uuid.UUID,
) -> bool:
    media = await get_event_media(session, event_id, media_id)
    if media is None:
        return False

    await session.delete(media)
    await session.commit()

    return True
