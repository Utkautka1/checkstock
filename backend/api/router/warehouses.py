"""
Роутер складов ФФ: CRUD + мягкое удаление.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.schemas import WarehouseCreate, WarehouseOut, WarehouseRename
from core.db import get_db
from core.deps import get_current_user
from db.psql.crud.warehouses import (
    create_warehouse,
    get_warehouse,
    get_warehouses,
    rename_warehouse,
    soft_delete_warehouse,
)

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


@router.get("", response_model=list[WarehouseOut])
async def list_warehouses(
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Список складов. include_deleted=true — включая удалённые."""
    return await get_warehouses(db, include_deleted=include_deleted)


@router.post("", response_model=WarehouseOut, status_code=201)
async def create(
    body: WarehouseCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Создаёт новый склад ФФ."""
    return await create_warehouse(db, body.name)


@router.patch("/{warehouse_id}", response_model=WarehouseOut)
async def rename(
    warehouse_id: int,
    body: WarehouseRename,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Переименовывает склад."""
    wh = await rename_warehouse(db, warehouse_id, body.name)
    if not wh:
        raise HTTPException(status_code=404, detail="Склад не найден")
    return wh


@router.delete("/{warehouse_id}", response_model=WarehouseOut)
async def delete(
    warehouse_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Мягкое удаление склада.
    Остатки и история сохраняются, склад помечается как неактивный.
    """
    wh = await soft_delete_warehouse(db, warehouse_id)
    if not wh:
        raise HTTPException(status_code=404, detail="Склад не найден или уже удалён")
    return wh
