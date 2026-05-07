from datetime import UTC, datetime, timedelta
import uuid
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Event
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
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        is_public=event_data.is_public,
        organization_id=event_data.organization_id,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


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

    stmt = select(Event).where(Event.id == event_id).options(selectinload(Event.media))
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
