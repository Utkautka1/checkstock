"""
CRUD для пользователей — только чтение, создание через seed-скрипт.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.psql.models.user import User


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Возвращает пользователя по username или None."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, username: str, hashed_password: str) -> User:
    """Создаёт пользователя (вызывается из seed-скрипта)."""
    user = User(username=username, hashed_password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
