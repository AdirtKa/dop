from pydantic import BaseModel, Field

from src.models.user import UserRole
from src.schemas.token import TokenResponse
from src.schemas.user import UserResponse


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(TokenResponse):
    user: UserResponse


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    role: UserRole = UserRole.EMPLOYEE