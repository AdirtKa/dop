"""Глобальная настройка access/error логирования для приложения."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import Request

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
ACCESS_LOG_PATH = LOG_DIR / "access.log"
ERROR_LOG_PATH = LOG_DIR / "error.log"

ACCESS_LOGGER_NAME = "app.access"
ERROR_LOGGER_NAME = "app.error"
_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 3


def _build_handler(path: Path, level: int) -> RotatingFileHandler:
    """Создаёт файловый handler с ротацией по размеру."""
    handler = RotatingFileHandler(
        filename=path,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    return handler


def _configure_named_logger(name: str, path: Path, level: int) -> logging.Logger:
    """Настраивает именованный логгер один раз на процесс."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False
    logger.addHandler(_build_handler(path, level))
    return logger


def setup_logging() -> None:
    """Инициализирует файловые логгеры приложения."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _configure_named_logger(ACCESS_LOGGER_NAME, ACCESS_LOG_PATH, logging.INFO)
    _configure_named_logger(ERROR_LOGGER_NAME, ERROR_LOG_PATH, logging.INFO)


def get_access_logger() -> logging.Logger:
    """Возвращает логгер для access-записей."""
    setup_logging()
    return logging.getLogger(ACCESS_LOGGER_NAME)


def get_error_logger() -> logging.Logger:
    """Возвращает логгер для ошибок приложения."""
    setup_logging()
    return logging.getLogger(ERROR_LOGGER_NAME)


def get_request_client(request: Request) -> str:
    """Возвращает IP клиента или заглушку, если адрес недоступен."""
    if request.client and request.client.host:
        return request.client.host
    return "unknown"
