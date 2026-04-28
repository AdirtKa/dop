from pydantic import BaseModel, ConfigDict
from uuid import UUID
from .mediafile import MediaFileRead


class EmployeeRead(BaseModel):
    id: UUID
    full_name: str
    position: str
    photo: MediaFileRead | None = None

    model_config = ConfigDict(from_attributes=True)
