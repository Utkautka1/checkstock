"""
Логгер — единая точка настройки логирования для всего проекта.
Использует стандартный logging с форматом, пригодным для Docker logs.
"""
import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Возвращает настроенный логгер с указанным именем подсистемы.
    Уровень берётся из переменной окружения LOG_LEVEL (по умолчанию INFO).
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
