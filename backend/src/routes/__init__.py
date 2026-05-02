"""Публичные экспорты API-роутеров."""

from .root import router as root_router
from .employee import router as employee_router
from .auth import auth_router

__all__: list[str] = ["root_router", "employee_router", "auth_router"]
