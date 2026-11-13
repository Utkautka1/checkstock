"""
Синглтон подключения к PostgreSQL через SQLAlchemy async.
Используется во всём приложении как единая точка доступа к БД.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

# Асинхронный движок — один на всё приложение
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,  # проверяет соединение перед использованием
)

# Фабрика сессий — не expire_on_commit, чтобы атрибуты были доступны после commit
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Базовый класс всех ORM-моделей."""
    pass


async def get_db() -> AsyncSession:
    """
    Dependency для FastAPI — открывает сессию и закрывает её после запроса.
    Гарантирует rollback при исключении.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
