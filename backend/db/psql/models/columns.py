"""
Переиспользуемые Annotated-типы колонок для SQLAlchemy.
Позволяют не дублировать определения первичных ключей, дат и строк.
"""
from datetime import datetime
from typing import Annotated

from sqlalchemy import DateTime, Integer, text
from sqlalchemy.orm import mapped_column

# Первичный ключ — автоинкремент
intpk = Annotated[int, mapped_column(Integer, primary_key=True, autoincrement=True)]

# Дата создания — проставляется автоматически на стороне БД
created_at = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    ),
]

# Строки ограниченной длины
str_32 = Annotated[str, 32]
str_64 = Annotated[str, 64]
str_255 = Annotated[str, 255]
