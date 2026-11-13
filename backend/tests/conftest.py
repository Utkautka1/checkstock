"""
Фикстуры для тестирования FastAPI с асинхронным SQLAlchemy.
Использует общий session-scoped event loop для избежания проблем с asyncpg connection pool.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from core.db import engine


@pytest_asyncio.fixture(loop_scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    await engine.dispose()
