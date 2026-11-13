"""
Сервис управления остатками — ядро бизнес-логики CheckStock.

Реализует все складские операции с гарантией согласованности:
  - Приход товара на склад
  - Перемещение между ФФ (create → ship → receive)
  - Резерв/снятие резерва FBS
  - Отправка FBS к клиенту
  - Отправка FBO на маркетплейс + приёмка

Ключевые инварианты:
  quantity_physical >= quantity_reserved >= 0
  quantity_available = quantity_physical - quantity_reserved
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import get_logger
from db.psql.crud.stock import add_operation, get_or_create_stock
from db.psql.models.enum import MovementStatus, OperationType, ShipmentStatus, ShipmentType
from db.psql.models.models import Movement, Shipment

log = get_logger("stock_service")


class StockService:
    """Сервис складского учёта — все мутации остатков проходят здесь."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def receive(self, product_id: int, warehouse_id: int, quantity: int) -> None:
        """
        Приход товара на склад ФФ.
        Увеличивает физический остаток на warehouse.
        """
        self._validate_positive(quantity)
        stock = await get_or_create_stock(self.db, product_id, warehouse_id)
        stock.quantity_physical += quantity

        await add_operation(
            self.db,
            product_id=product_id,
            operation_type=OperationType.RECEIPT,
            quantity=quantity,
            warehouse_to_id=warehouse_id,
            comment=f"Приход: {quantity} ед.",
        )
        await self.db.commit()
        log.info(f"✅ Приход: product={product_id}, wh={warehouse_id}, qty={quantity}")

    async def create_movement(
        self, product_id: int, from_wh: int, to_wh: int, quantity: int
    ) -> Movement:
        """
        Создаёт перемещение и списывает физически со склада-источника.
        Статус → IN_TRANSIT. Товар числится «в пути».
        """
        self._validate_positive(quantity)
        stock = await get_or_create_stock(self.db, product_id, from_wh)
        available = stock.quantity_physical - stock.quantity_reserved
        if available < quantity:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Нехватка: доступно {available}, нужно {quantity}. "
                       f"Всего физически: {stock.quantity_physical}, в резерве: {stock.quantity_reserved}",
            )
        # Списываем физически — товар покидает склад
        stock.quantity_physical -= quantity

        movement = Movement(
            product_id=product_id,
            warehouse_from_id=from_wh,
            warehouse_to_id=to_wh,
            quantity=quantity,
            status=MovementStatus.IN_TRANSIT,
        )
        self.db.add(movement)
        await self.db.flush()

        await add_operation(
            self.db,
            product_id=product_id,
            operation_type=OperationType.MOVEMENT_OUT,
            quantity=quantity,
            warehouse_from_id=from_wh,
            warehouse_to_id=to_wh,
            movement_id=movement.id,
        )
        await self.db.commit()
        log.info(f"📦 Перемещение создано: id={movement.id}, от wh={from_wh} к wh={to_wh}, qty={quantity}")
        return movement

    async def confirm_movement(self, movement_id: int) -> Movement:
        """
        Подтверждение приёмки перемещения на складе-получателе.

        Идемпотентность: повторный вызов на уже completed движении
        не списывает товар дважды — возвращает движение как есть.
        """
        result = await self.db.execute(
            select(Movement).where(Movement.id == movement_id)
        )
        movement = result.scalar_one_or_none()
        if not movement:
            raise HTTPException(status_code=404, detail="Перемещение не найдено")

        # Идемпотентность — уже подтверждено, ничего не делаем
        if movement.status == MovementStatus.COMPLETED:
            log.debug(f"Повторное подтверждение movement={movement_id} — игнорируем")
            return movement

        if movement.status != MovementStatus.IN_TRANSIT:
            raise HTTPException(
                status_code=422,
                detail=f"Невозможно подтвердить движение в статусе {movement.status}",
            )

        # Зачисляем товар на склад-получатель
        stock = await get_or_create_stock(self.db, movement.product_id, movement.warehouse_to_id)
        stock.quantity_physical += movement.quantity

        movement.status = MovementStatus.COMPLETED
        movement.completed_at = datetime.now(timezone.utc)

        await add_operation(
            self.db,
            product_id=movement.product_id,
            operation_type=OperationType.MOVEMENT_IN,
            quantity=movement.quantity,
            warehouse_from_id=movement.warehouse_from_id,
            warehouse_to_id=movement.warehouse_to_id,
            movement_id=movement.id,
        )
        await self.db.commit()
        log.info(f"✅ Перемещение подтверждено: id={movement_id}")
        return movement

    async def reserve_fbs(self, product_id: int, warehouse_id: int, quantity: int) -> Shipment:
        """
        Резервирует товар под FBS-отправку. Уменьшает quantity_available,
        физический остаток не меняется — товар ещё на складе.
        """
        self._validate_positive(quantity)
        stock = await get_or_create_stock(self.db, product_id, warehouse_id)
        available = stock.quantity_physical - stock.quantity_reserved

        if available < quantity:
            raise HTTPException(
                status_code=422,
                detail=f"Нехватка для резерва FBS: доступно {available}, нужно {quantity}",
            )

        stock.quantity_reserved += quantity
        shipment = Shipment(
            product_id=product_id,
            warehouse_id=warehouse_id,
            shipment_type=ShipmentType.FBS,
            status=ShipmentStatus.RESERVED,
            quantity=quantity,
        )
        self.db.add(shipment)
        await self.db.flush()

        await add_operation(
            self.db,
            product_id=product_id,
            operation_type=OperationType.RESERVE_FBS,
            quantity=quantity,
            warehouse_from_id=warehouse_id,
            shipment_id=shipment.id,
        )
        await self.db.commit()
        log.info(f"🔒 FBS резерв: product={product_id}, wh={warehouse_id}, qty={quantity}")
        return shipment

    async def ship_fbs(self, shipment_id: int) -> Shipment:
        """
        Отправка FBS: снимает резерв и физический остаток.
        Товар покидает ФФ и едёт к клиенту (статус → SHIPPED).
        """
        shipment = await self._get_shipment(shipment_id, ShipmentType.FBS, ShipmentStatus.RESERVED)
        stock = await get_or_create_stock(self.db, shipment.product_id, shipment.warehouse_id)

        stock.quantity_reserved -= shipment.quantity
        stock.quantity_physical -= shipment.quantity

        shipment.status = ShipmentStatus.SHIPPED
        shipment.shipped_at = datetime.now(timezone.utc)

        await add_operation(
            self.db,
            product_id=shipment.product_id,
            operation_type=OperationType.SHIP_FBS,
            quantity=shipment.quantity,
            warehouse_from_id=shipment.warehouse_id,
            shipment_id=shipment.id,
        )
        await self.db.commit()
        log.info(f"🚚 FBS отправлено: shipment={shipment_id}")
        return shipment

    async def ship_fbo(self, product_id: int, warehouse_id: int, quantity: int) -> Shipment:
        """
        FBO отправка: товар покидает ФФ, числится в пути до приёмки маркетплейсом.
        Обрабатываем нехватку на выбранном ФФ при достаточном общем остатке.
        """
        self._validate_positive(quantity)
        stock = await get_or_create_stock(self.db, product_id, warehouse_id)
        available = stock.quantity_physical - stock.quantity_reserved

        if available < quantity:
            raise HTTPException(
                status_code=422,
                detail=f"Нехватка на складе: доступно {available}, нужно {quantity}. "
                       f"Проверьте другие склады или оформите перемещение.",
            )

        stock.quantity_physical -= quantity
        shipment = Shipment(
            product_id=product_id,
            warehouse_id=warehouse_id,
            shipment_type=ShipmentType.FBO,
            status=ShipmentStatus.SHIPPED,  # FBO сразу в пути (нет этапа резерва)
            quantity=quantity,
        )
        self.db.add(shipment)
        await self.db.flush()

        await add_operation(
            self.db,
            product_id=product_id,
            operation_type=OperationType.SHIP_FBO,
            quantity=quantity,
            warehouse_from_id=warehouse_id,
            shipment_id=shipment.id,
        )
        await self.db.commit()
        log.info(f"📤 FBO отправлено: product={product_id}, wh={warehouse_id}, qty={quantity}")
        return shipment

    async def receive_fbo(self, shipment_id: int) -> Shipment:
        """
        Приёмка FBO маркетплейсом: товар больше не числится в пути.
        Статус → DELIVERED.
        """
        shipment = await self._get_shipment(shipment_id, ShipmentType.FBO, ShipmentStatus.SHIPPED)
        shipment.status = ShipmentStatus.DELIVERED
        shipment.delivered_at = datetime.now(timezone.utc)

        await add_operation(
            self.db,
            product_id=shipment.product_id,
            operation_type=OperationType.RECEIVE_FBO,
            quantity=shipment.quantity,
            warehouse_from_id=shipment.warehouse_id,
            shipment_id=shipment.id,
            comment="Принято маркетплейсом",
        )
        await self.db.commit()
        log.info(f"✅ FBO принято маркетплейсом: shipment={shipment_id}")
        return shipment

    async def cancel_shipment(self, shipment_id: int) -> Shipment:
        """
        Отмена отправки FBS (только в статусе RESERVED — ещё не отправлено).
        Возвращает товар в доступный остаток.
        """
        result = await self.db.execute(select(Shipment).where(Shipment.id == shipment_id))
        shipment = result.scalar_one_or_none()
        if not shipment:
            raise HTTPException(status_code=404, detail="Отправка не найдена")
        if shipment.status != ShipmentStatus.RESERVED:
            raise HTTPException(status_code=422, detail="Можно отменить только зарезервированную отправку")

        stock = await get_or_create_stock(self.db, shipment.product_id, shipment.warehouse_id)
        stock.quantity_reserved -= shipment.quantity
        shipment.status = ShipmentStatus.CANCELLED

        await add_operation(
            self.db,
            product_id=shipment.product_id,
            operation_type=OperationType.CANCEL_SHIPMENT,
            quantity=shipment.quantity,
            warehouse_to_id=shipment.warehouse_id,
            shipment_id=shipment.id,
        )
        await self.db.commit()
        log.info(f"❌ Отправка отменена: shipment={shipment_id}")
        return shipment

    # ── Вспомогательные методы ──────────────────────────────────────────────

    async def _get_shipment(
        self, shipment_id: int, expected_type: ShipmentType, expected_status: ShipmentStatus
    ) -> Shipment:
        """Загружает отправку и проверяет тип и статус."""
        result = await self.db.execute(select(Shipment).where(Shipment.id == shipment_id))
        shipment = result.scalar_one_or_none()
        if not shipment:
            raise HTTPException(status_code=404, detail="Отправка не найдена")
        if shipment.shipment_type != expected_type:
            raise HTTPException(status_code=422, detail=f"Ожидается тип {expected_type}")
        if shipment.status != expected_status:
            raise HTTPException(
                status_code=422,
                detail=f"Статус {shipment.status}, ожидается {expected_status}",
            )
        return shipment

    @staticmethod
    def _validate_positive(quantity: int) -> None:
        """Количество должно быть положительным."""
        if quantity <= 0:
            raise HTTPException(status_code=422, detail="Количество должно быть > 0")
