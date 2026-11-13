"""
Роутер перемещений между складами ФФ.
Оформление, подтверждение приёмки, список.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.schemas import MovementCreate, MovementOut
from core.db import get_db
from core.deps import get_current_user
from db.psql.models.models import Movement
from services.stock_service import StockService

router = APIRouter(prefix="/movements", tags=["movements"])


@router.get("", response_model=list[MovementOut])
async def list_movements(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Список всех перемещений."""
    result = await db.execute(
        select(Movement).order_by(Movement.created_at.desc()).limit(200)
    )
    return list(result.scalars().all())


@router.post("", response_model=MovementOut, status_code=201)
async def create_movement(
    body: MovementCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Создаёт перемещение: списывает товар со склада-источника,
    переводит в статус IN_TRANSIT (в пути).
    """
    svc = StockService(db)
    return await svc.create_movement(
        body.product_id, body.warehouse_from_id, body.warehouse_to_id, body.quantity
    )


@router.post("/{movement_id}/confirm", response_model=MovementOut)
async def confirm_movement(
    movement_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Подтверждение приёмки на складе-получателе.
    Идемпотентно: повторный вызов безопасен.
    """
    svc = StockService(db)
    return await svc.confirm_movement(movement_id)
