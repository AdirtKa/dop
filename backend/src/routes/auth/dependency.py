import uuid

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette import status

from src.models import User
from src.models.user import UserRole
from src.routes.auth.security import decode_access_token
from src.session import get_session

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)

        if payload.get("type") != "access":
            raise credentials_exception

        user_id = uuid.UUID(payload["sub"])

    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise credentials_exception

    user = await session.get(User, user_id)

    if user is None or not user.is_active:
        raise credentials_exception

    return user


def require_roles(*allowed_roles: UserRole):
    async def checker(
            current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        return current_user

    return checker
