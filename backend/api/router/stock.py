"""
Роутер экрана остатков — главный экран CheckStock.
Показывает все товары по всем складам с тремя показателями.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.schemas import ProductOut, ReceiveRequest, StockItemOut
from core.db import get_db
from core.deps import get_current_user
from db.psql.crud.products import get_products
from db.psql.crud.stock import get_operations, get_stocks_with_details
from api.schemas.schemas import OperationOut
from services.stock_service import StockService

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("", response_model=list[StockItemOut])
async def get_stock(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Экран остатков: все товары × все склады.
    Возвращает физический остаток, резерв и доступное количество.
    """
    stocks = await get_stocks_with_details(db)
    result = []
    for s in stocks:
        result.append(StockItemOut(
            product_id=s.product_id,
            product_sku=s.product.sku,
            product_name=s.product.name,
            warehouse_id=s.warehouse_id,
            warehouse_name=s.warehouse.name,
            warehouse_active=s.warehouse.is_active,
            quantity_physical=s.quantity_physical,
            quantity_reserved=s.quantity_reserved,
            quantity_available=s.quantity_physical - s.quantity_reserved,
        ))
    return result


@router.post("/receive", response_model=dict, status_code=201)
async def receive(
    body: ReceiveRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Оформляет приход товара на склад ФФ."""
    svc = StockService(db)
    await svc.receive(body.product_id, body.warehouse_id, body.quantity)
    return {"ok": True}


@router.get("/products", response_model=list[ProductOut])
async def list_products(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Справочник товаров."""
    return await get_products(db)


@router.get("/operations", response_model=list[OperationOut])
async def list_operations(
    product_id: int | None = None,
    warehouse_id: int | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """История операций с опциональной фильтрацией по товару и складу."""
    ops = await get_operations(db, product_id=product_id, warehouse_id=warehouse_id, limit=limit)
    result = []
    for op in ops:
        result.append(OperationOut(
            id=op.id,
            product_id=op.product_id,
            product_sku=op.product.sku if op.product else None,
            product_name=op.product.name if op.product else None,
            warehouse_from_id=op.warehouse_from_id,
            warehouse_to_id=op.warehouse_to_id,
            operation_type=op.operation_type,
            quantity=op.quantity,
            comment=op.comment,
            created_at=op.created_at,
        ))
    return result
