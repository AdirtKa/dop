from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.employee import get_employees
from src.schemas.employee import EmployeeRead
from src.session import get_session

router = APIRouter()
SessionDependency = Annotated[AsyncSession, Depends(get_session)]


@router.get("/", response_model=List[EmployeeRead])
async def read_employees(session: SessionDependency):
    try:
        employees = await get_employees(session)
        return employees
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load employees",
        )
