from datetime import datetime
from typing import Self
import uuid

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.schemas.mediafile import MediaFileRead


class OrganizationShortRead(BaseModel):
    id: uuid.UUID
    name: str = Field(validation_alias="full_name")

    model_config = ConfigDict(from_attributes=True)


class ReadEventResponse(BaseModel):
    id: uuid.UUID
    name: str
    start_time: datetime
    end_time: datetime
    organization: OrganizationShortRead | None
    media: list[MediaFileRead]


ALLOWED_EVENT_MEDIA_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "video/mp4",
    "video/webm",
}


class EventMediaCreateRequest(BaseModel):
    filename: str
    content_type: str

    @model_validator(mode="after")
    def validate_content_type(self) -> Self:
        if self.content_type not in ALLOWED_EVENT_MEDIA_TYPES:
            raise ValueError("Недопустимый тип файла")
        return self


class EventCreateRequest(BaseModel):
    name: str
    start_time: datetime
    end_time: datetime
    is_public: bool = False
    organization_id: uuid.UUID | None = None
    media: list[EventMediaCreateRequest] = Field(default_factory=list)


class EventMediaUploadResponse(BaseModel):
    media_file: MediaFileRead
    presigned_url: str


class EventMediaUploadError(BaseModel):
    filename: str
    detail: str


class EventPutResponse(BaseModel):
    id: uuid.UUID
    name: str
    start_time: datetime
    end_time: datetime
    is_public: bool
    organization: OrganizationShortRead | None
    media: list[MediaFileRead]
    upload_urls: list[EventMediaUploadResponse] = Field(default_factory=list)
    upload_errors: list[EventMediaUploadError] = Field(default_factory=list)


class EventPatchRequest(BaseModel):
    name: str
    start_time: datetime
    end_time: datetime
    organization_id: uuid.UUID | None


class EventVisibilityPatchRequest(BaseModel):
    is_public: bool
