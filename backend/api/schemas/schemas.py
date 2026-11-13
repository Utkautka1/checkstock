"""
Pydantic-схемы для запросов и ответов CheckStock API.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from db.psql.models.enum import MovementStatus, OperationType, ShipmentStatus, ShipmentType


# ── Auth ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Products ────────────────────────────────────────────────────────────────

class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    name: str


# ── Warehouses ──────────────────────────────────────────────────────────────

class WarehouseCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Название склада не может быть пустым")
        return v.strip()


class WarehouseRename(BaseModel):
    name: str


class WarehouseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    is_active: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime


# ── Stock ────────────────────────────────────────────────────────────────────

class StockItemOut(BaseModel):
    """Остаток одного товара на одном складе."""
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    product_sku: str
    product_name: str
    warehouse_id: int
    warehouse_name: str
    warehouse_active: bool
    quantity_physical: int
    quantity_reserved: int
    quantity_available: int  # вычисляется


class ReceiveRequest(BaseModel):
    product_id: int
    warehouse_id: int
    quantity: int


# ── Movements ───────────────────────────────────────────────────────────────

class MovementCreate(BaseModel):
    product_id: int
    warehouse_from_id: int
    warehouse_to_id: int
    quantity: int


class MovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    warehouse_from_id: int
    warehouse_to_id: int
    quantity: int
    status: MovementStatus
    created_at: datetime
    completed_at: Optional[datetime] = None


# ── Shipments ────────────────────────────────────────────────────────────────

class FBSReserveRequest(BaseModel):
    product_id: int
    warehouse_id: int
    quantity: int


class FBOShipRequest(BaseModel):
    product_id: int
    warehouse_id: int
    quantity: int


class ShipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    warehouse_id: int
    shipment_type: ShipmentType
    status: ShipmentStatus
    quantity: int
    created_at: datetime
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


# ── Operations (history) ────────────────────────────────────────────────────

class OperationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    product_sku: Optional[str] = None
    product_name: Optional[str] = None
    warehouse_from_id: Optional[int] = None
    warehouse_to_id: Optional[int] = None
    operation_type: OperationType
    quantity: int
    comment: Optional[str] = None
    created_at: datetime
