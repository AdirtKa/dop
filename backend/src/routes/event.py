from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.logger import get_error_logger
from src.models import Event, User, UserRole
from src.repository.event import add_event, get_events, patch_event
from src.repository.media import attach_event_media
from src.routes.auth.auth import session_dependency
from src.routes.auth.dependency import get_current_user, get_optional_current_user
from src.schemas import (
    EventCreateRequest,
    EventMediaUploadResponse,
    EventPutResponse,
    MediaFileRead,
    ReadEventResponse,
)
from src.schemas.event import EventMediaUploadError, EventPatchRequest, OrganizationShortRead
from src.services.media import build_media_payload, get_media_kind_by_content_type

router: APIRouter = APIRouter()

ALLOWED_EVENT_MEDIA_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "video/mp4",
    "video/webm",
}

error_logger = get_error_logger()


@router.get("/", response_model=list[ReadEventResponse])
async def read_events(
    session: session_dependency,
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    try:
        if current_user is None:
            return await get_events(
                session=session,
                limit=limit,
                offset=offset,
                is_public=True,
                is_finished=True,
            )

        if current_user.role == UserRole.ORGANIZATION:
            return await get_events(
                session=session,
                limit=limit,
                offset=offset,
                is_public=True,
                is_finished=True,
                organization_id=current_user.id,
                include_own_events=True,
            )

        if current_user.role in {UserRole.EMPLOYEE, UserRole.ADMIN}:
            return await get_events(session, limit, offset)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your role is undefined",
        )
    except HTTPException:
        raise
    except Exception as exc:
        error_logger.exception("Failed to load events list", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load events",
        ) from exc


@router.post("/", response_model=EventPutResponse)
async def create_event(
    session: session_dependency,
    event_data: EventCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        data = event_data.model_copy()

        if current_user.role == UserRole.ORGANIZATION:
            data = data.model_copy(update={"organization_id": current_user.id})

        elif current_user.role not in {UserRole.EMPLOYEE, UserRole.ADMIN}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to create events",
            )

        event: Event = await add_event(session, data)

    except HTTPException:
        raise

    except Exception as exc:
        error_logger.exception("Failed to create event", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event",
        ) from exc

    media_uploads: list[MediaFileRead] = []
    upload_urls: list[EventMediaUploadResponse] = []
    upload_errors: list[EventMediaUploadError] = []

    for media in event_data.media:
        try:
            storage_key, presigned_url, public_url = build_media_payload(
                filename=media.filename,
                storage_prefix=f"events/{event.id}",
            )

            event, attached_media = await attach_event_media(
                session=session,
                event=event,
                storage_key=storage_key,
                public_url=public_url,
                mime_type=media.content_type,
                media_kind=get_media_kind_by_content_type(media.content_type),
            )

            media_file_read = MediaFileRead.model_validate(attached_media)

            media_uploads.append(media_file_read)
            upload_urls.append(
                EventMediaUploadResponse(
                    media_file=media_file_read,
                    presigned_url=presigned_url,
                )
            )

        except Exception as exc:
            await session.rollback()

            error_logger.exception(
                "Failed to attach event media",
                exc_info=exc,
            )

            upload_errors.append(
                EventMediaUploadError(
                    filename=media.filename,
                    detail="Failed to prepare media upload",
                )
            )

    return EventPutResponse(
        id=event.id,
        name=event.name,
        start_time=event.start_time,
        end_time=event.end_time,
        is_public=event.is_public,
        organization=(
            OrganizationShortRead.model_validate(event.organization)
            if event.organization is not None
            else None
        ),
        media=media_uploads,
        upload_urls=upload_urls,
        upload_errors=upload_errors,
    )


@router.patch("/{event_id}", response_model=ReadEventResponse)
async def update_event(
    session: session_dependency,
    event_id: uuid.UUID,
    event_data: EventPatchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        if current_user.role == UserRole.ORGANIZATION:
            data = event_data.model_copy(update={"organization_id": current_user.id})
        else:
            data = event_data.model_copy()

        event = await patch_event(session, event_id, data)
        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to update employee",
            )
        return event
    except HTTPException:
        raise
    except Exception as exc:
        error_logger.exception("Failed to update event", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update event",
        ) from exc
