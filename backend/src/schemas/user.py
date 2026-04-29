import uuid

from pydantic import BaseModel

from src.models.user import UserRole
from src.schemas.token import TokenResponse


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str





class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRole
    is_active: bool

    model_config = {
        "from_attributes": True,
    }



