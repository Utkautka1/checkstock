"""
Роутер отправок FBS и FBO.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.schemas import FBOShipRequest, FBSReserveRequest, ShipmentOut
from core.db import get_db
from core.deps import get_current_user
from db.psql.models.models import Shipment
from services.stock_service import StockService

router = APIRouter(prefix="/shipments", tags=["shipments"])


@router.get("", response_model=list[ShipmentOut])
async def list_shipments(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Список всех отправок (FBS + FBO)."""
    result = await db.execute(
        select(Shipment).order_by(Shipment.created_at.desc()).limit(200)
    )
    return list(result.scalars().all())


@router.post("/fbs/reserve", response_model=ShipmentOut, status_code=201)
async def reserve_fbs(
    body: FBSReserveRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Резервирует товар под FBS-отправку. Блокирует количество на складе."""
    svc = StockService(db)
    return await svc.reserve_fbs(body.product_id, body.warehouse_id, body.quantity)


@router.post("/fbs/{shipment_id}/ship", response_model=ShipmentOut)
async def ship_fbs(
    shipment_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Отправка FBS клиенту: снимает резерв и физический остаток."""
    svc = StockService(db)
    return await svc.ship_fbs(shipment_id)


@router.post("/fbs/{shipment_id}/cancel", response_model=ShipmentOut)
async def cancel_fbs(
    shipment_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Отмена FBS резерва: возвращает товар в доступный остаток."""
    svc = StockService(db)
    return await svc.cancel_shipment(shipment_id)


@router.post("/fbo/ship", response_model=ShipmentOut, status_code=201)
async def ship_fbo(
    body: FBOShipRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Отправка FBO: товар покидает ФФ и едёт на склад маркетплейса."""
    svc = StockService(db)
    return await svc.ship_fbo(body.product_id, body.warehouse_id, body.quantity)


@router.post("/fbo/{shipment_id}/receive", response_model=ShipmentOut)
async def receive_fbo(
    shipment_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Приёмка FBO маркетплейсом: товар больше не числится в пути."""
    svc = StockService(db)
    return await svc.receive_fbo(shipment_id)
