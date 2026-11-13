"""
CRUD склады фулфилмента (ФФ).

Мягкое удаление: is_active=False + deleted_at — история и остатки сохраняются.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.psql.models.models import Warehouse


async def get_warehouses(db: AsyncSession, include_deleted: bool = False) -> list[Warehouse]:
    """Список складов. По умолчанию — только активные."""
    stmt = select(Warehouse)
    if not include_deleted:
        stmt = stmt.where(Warehouse.is_active == True)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_warehouse(db: AsyncSession, warehouse_id: int) -> Warehouse | None:
    """Склад по ID (любой, включая удалённый)."""
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    return result.scalar_one_or_none()


async def create_warehouse(db: AsyncSession, name: str) -> Warehouse:
    """Создаёт новый склад ФФ."""
    wh = Warehouse(name=name)
    db.add(wh)
    await db.commit()
    await db.refresh(wh)
    return wh


async def rename_warehouse(db: AsyncSession, warehouse_id: int, new_name: str) -> Warehouse | None:
    """Переименовывает склад. Возвращает None если не найден."""
    wh = await get_warehouse(db, warehouse_id)
    if not wh:
        return None
    wh.name = new_name
    await db.commit()
    await db.refresh(wh)
    return wh


async def soft_delete_warehouse(db: AsyncSession, warehouse_id: int) -> Warehouse | None:
    """
    Мягкое удаление: помечает склад как неактивный.
    Остатки и история операций сохраняются в БД.
    """
    wh = await get_warehouse(db, warehouse_id)
    if not wh or not wh.is_active:
        return None
    wh.is_active = False
    wh.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(wh)
    return wh
