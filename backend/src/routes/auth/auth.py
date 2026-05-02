from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from src.schemas.auth import LoginRequest, LoginResponse
from src.schemas.token import TokenResponse
from src.services.auth import login_user, logout_user, refresh_tokens
from src.session import get_session

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
        data: LoginRequest,
        request: Request,
        response: Response,
        session: AsyncSession = Depends(get_session),
):
    return await login_user(
        session=session,
        request=request,
        response=response,
        username=data.username,
        password=data.password,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
        request: Request,
        response: Response,
        session: AsyncSession = Depends(get_session),
):
    return await refresh_tokens(
        session=session,
        request=request,
        response=response,
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    return await logout_user(
        session=session,
        request=request,
        response=response,
    )
