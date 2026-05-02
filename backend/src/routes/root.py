"""Корневые служебные маршруты приложения."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Возвращает простой health-check ответ."""
    return {"status": "ok"}
