"""
Перечисления для полей БД CheckStock.
"""
import enum


class MovementStatus(str, enum.Enum):
    """Статус перемещения товара между складами ФФ."""
    PENDING = "pending"       # Создано, ещё не подтверждено
    IN_TRANSIT = "in_transit" # В пути
    COMPLETED = "completed"   # Принято на складе назначения
    CANCELLED = "cancelled"   # Отменено


class ShipmentType(str, enum.Enum):
    """Тип отправки."""
    FBS = "fbs"  # Fulfillment by Seller — к клиенту
    FBO = "fbo"  # Fulfillment by Operator — на склад маркетплейса


class ShipmentStatus(str, enum.Enum):
    """Статус отправки."""
    RESERVED = "reserved"     # FBS: зарезервировано на ФФ
    SHIPPED = "shipped"       # Отправлено (едет к клиенту или маркетплейсу)
    DELIVERED = "delivered"   # FBO: принято маркетплейсом / FBS: доставлено клиенту
    CANCELLED = "cancelled"   # Отменено — возврат в остаток


class OperationType(str, enum.Enum):
    """Тип операции для истории движений."""
    RECEIPT = "receipt"           # Приход товара на склад
    MOVEMENT_OUT = "movement_out" # Отправка при перемещении между ФФ
    MOVEMENT_IN = "movement_in"   # Приёмка при перемещении между ФФ
    RESERVE_FBS = "reserve_fbs"   # Резервирование под FBS
    UNRESERVE_FBS = "unreserve_fbs"  # Снятие резерва FBS
    SHIP_FBS = "ship_fbs"         # Отправка FBS к клиенту
    SHIP_FBO = "ship_fbo"         # Отправка FBO на маркетплейс
    RECEIVE_FBO = "receive_fbo"   # Приёмка FBO маркетплейсом
    CANCEL_SHIPMENT = "cancel_shipment"  # Отмена отправки
    WAREHOUSE_DELETED = "warehouse_deleted"  # Склад удалён
