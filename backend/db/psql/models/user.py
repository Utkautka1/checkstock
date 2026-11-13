"""
Модель пользователя — только для авторизации.
В рамках тестового задания достаточно одной учётной записи менеджера.
"""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base
from db.psql.models.columns import created_at, intpk, str_64


class User(Base):
    """Пользователь системы — менеджер склада."""

    __tablename__ = "users"

    id: Mapped[intpk]
    username: Mapped[str_64] = mapped_column(String(64), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[created_at]
