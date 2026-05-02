"""Публичные экспорты API-роутеров."""

from .auth import auth_router
from .employee import router as employee_router
from .root import router as root_router

__all__: list[str] = ["auth_router", "employee_router", "root_router"]
