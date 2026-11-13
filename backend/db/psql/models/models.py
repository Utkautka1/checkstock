"""
Модели таблиц CheckStock.

Схема:
  products      — справочник товаров (артикул + название)
  warehouses    — склады фулфилмента (ФФ), поддерживают мягкое удаление
  stock         — остатки: физически / доступно / резерв FBS
  stock_operations — история всех операций (аудит)
  movements     — перемещения между ФФ
  shipments     — отправки FBS/FBO
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from db.psql.models.columns import created_at, intpk, str_32, str_64, str_255
from db.psql.models.enum import (
    MovementStatus,
    OperationType,
    ShipmentStatus,
    ShipmentType,
)


class Product(Base):
    """Справочник товаров."""

    __tablename__ = "products"

    id: Mapped[intpk]
    sku: Mapped[str_32] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str_255] = mapped_column(String(255), nullable=False)
    created_at: Mapped[created_at]

    stocks: Mapped[list["Stock"]] = relationship(back_populates="product")
    operations: Mapped[list["StockOperation"]] = relationship(back_populates="product")


class Warehouse(Base):
    """
    Склад фулфилмента (ФФ).

    Поддерживает мягкое удаление: при удалении is_active=False,
    остатки и история сохраняются.
    """

    __tablename__ = "warehouses"

    id: Mapped[intpk]
    name: Mapped[str_64] = mapped_column(String(64), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    # Дата деактивации — чтобы знать, когда склад был «удалён»
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[created_at]

    stocks: Mapped[list["Stock"]] = relationship(back_populates="warehouse")


class Stock(Base):
    """
    Остаток конкретного товара на конкретном складе ФФ.

    Три показателя:
      quantity_physical — физически на складе (total)
      quantity_reserved — зарезервировано под FBS (ещё не отправлено)
      quantity_available = quantity_physical - quantity_reserved
    """

    __tablename__ = "stock"
    __table_args__ = (UniqueConstraint("product_id", "warehouse_id"),)

    id: Mapped[intpk]
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)

    quantity_physical: Mapped[int] = mapped_column(default=0, nullable=False)
    quantity_reserved: Mapped[int] = mapped_column(default=0, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="stocks")
    warehouse: Mapped["Warehouse"] = relationship(back_populates="stocks")


class StockOperation(Base):
    """
    Журнал всех операций с остатками — аудит и история.

    Каждая операция: что, сколько, откуда, куда, когда и почему.
    """

    __tablename__ = "stock_operations"

    id: Mapped[intpk]
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    # Склад-источник (None — если операция прихода)
    warehouse_from_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouses.id"), nullable=True)
    # Склад-получатель (None — если операция отправки к клиенту)
    warehouse_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouses.id"), nullable=True)

    operation_type: Mapped[OperationType] = mapped_column(Enum(OperationType), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Ссылки на связанные сущности (опционально — для трассировки)
    movement_id: Mapped[Optional[int]] = mapped_column(ForeignKey("movements.id"), nullable=True)
    shipment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shipments.id"), nullable=True)

    created_at: Mapped[created_at]

    product: Mapped["Product"] = relationship(back_populates="operations")


class Movement(Base):
    """
    Перемещение товара между складами ФФ.

    Статусы: pending → in_transit → completed / cancelled
    Повторное подтверждение (completed → completed) не списывает товар дважды
    — проверяется на уровне сервиса.
    """

    __tablename__ = "movements"

    id: Mapped[intpk]
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    warehouse_from_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    warehouse_to_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)

    quantity: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[MovementStatus] = mapped_column(
        Enum(MovementStatus), default=MovementStatus.PENDING, nullable=False
    )
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[created_at]
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Shipment(Base):
    """
    Отправка FBS (к клиенту) или FBO (на склад маркетплейса).

    FBS: RESERVED → SHIPPED → DELIVERED / CANCELLED
    FBO: RESERVED → SHIPPED → DELIVERED (приёмка маркетплейсом)
    """

    __tablename__ = "shipments"

    id: Mapped[intpk]
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)

    shipment_type: Mapped[ShipmentType] = mapped_column(Enum(ShipmentType), nullable=False)
    status: Mapped[ShipmentStatus] = mapped_column(
        Enum(ShipmentStatus), default=ShipmentStatus.RESERVED, nullable=False
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[created_at]
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
