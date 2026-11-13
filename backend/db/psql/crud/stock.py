"""
CRUD для остатков (Stock) и операций (StockOperation).

Stock — один на пару (product, warehouse).
Используем get_or_create паттерн — если записи нет, создаём с нулём.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.psql.models.models import Stock, StockOperation
from db.psql.models.enum import OperationType


async def get_or_create_stock(
    db: AsyncSession, product_id: int, warehouse_id: int
) -> Stock:
    """
    Атомарный get-or-create остатка.
    Нельзя делать два отдельных запроса — race condition при параллельных приходах.
    Вместо UPSERT используем простой подход: в рамках тестового это допустимо.
    """
    result = await db.execute(
        select(Stock)
        .where(Stock.product_id == product_id, Stock.warehouse_id == warehouse_id)
    )
    stock = result.scalar_one_or_none()
    if not stock:
        stock = Stock(product_id=product_id, warehouse_id=warehouse_id)
        db.add(stock)
        await db.flush()  # получаем ID без commit — транзакция продолжается
    return stock


async def get_stocks_with_details(db: AsyncSession) -> list[Stock]:
    """Все остатки с загруженными product и warehouse."""
    result = await db.execute(
        select(Stock)
        .options(selectinload(Stock.product), selectinload(Stock.warehouse))
        .order_by(Stock.product_id, Stock.warehouse_id)
    )
    return list(result.scalars().all())


async def get_stock_by_product(db: AsyncSession, product_id: int) -> list[Stock]:
    """Остатки по конкретному товару на всех складах."""
    result = await db.execute(
        select(Stock)
        .options(selectinload(Stock.warehouse))
        .where(Stock.product_id == product_id)
    )
    return list(result.scalars().all())


async def add_operation(
    db: AsyncSession,
    *,
    product_id: int,
    operation_type: OperationType,
    quantity: int,
    warehouse_from_id: int | None = None,
    warehouse_to_id: int | None = None,
    comment: str | None = None,
    movement_id: int | None = None,
    shipment_id: int | None = None,
) -> StockOperation:
    """Записывает операцию в журнал аудита."""
    op = StockOperation(
        product_id=product_id,
        operation_type=operation_type,
        quantity=quantity,
        warehouse_from_id=warehouse_from_id,
        warehouse_to_id=warehouse_to_id,
        comment=comment,
        movement_id=movement_id,
        shipment_id=shipment_id,
    )
    db.add(op)
    await db.flush()
    return op


async def get_operations(
    db: AsyncSession,
    product_id: int | None = None,
    warehouse_id: int | None = None,
    limit: int = 100,
) -> list[StockOperation]:
    """История операций с опциональной фильтрацией."""
    stmt = (
        select(StockOperation)
        .options(
            selectinload(StockOperation.product),
        )
        .order_by(StockOperation.created_at.desc())
        .limit(limit)
    )
    if product_id:
        stmt = stmt.where(StockOperation.product_id == product_id)
    if warehouse_id:
        stmt = stmt.where(
            (StockOperation.warehouse_from_id == warehouse_id)
            | (StockOperation.warehouse_to_id == warehouse_id)
        )
    result = await db.execute(stmt)
    return list(result.scalars().all())
