// Типы данных, соответствующие Pydantic-схемам backend

export interface Product {
  id: number
  sku: string
  name: string
}

export interface Warehouse {
  id: number
  name: string
  is_active: boolean
  deleted_at: string | null
  created_at: string
}

export interface StockItem {
  product_id: number
  product_sku: string
  product_name: string
  warehouse_id: number
  warehouse_name: string
  warehouse_active: boolean
  quantity_physical: number
  quantity_reserved: number
  quantity_available: number
}

export type MovementStatus = 'pending' | 'in_transit' | 'completed' | 'cancelled'
export type ShipmentType = 'fbs' | 'fbo'
export type ShipmentStatus = 'reserved' | 'shipped' | 'delivered' | 'cancelled'

export interface Movement {
  id: number
  product_id: number
  warehouse_from_id: number
  warehouse_to_id: number
  quantity: number
  status: MovementStatus
  created_at: string
  completed_at: string | null
}

export interface Shipment {
  id: number
  product_id: number
  warehouse_id: number
  shipment_type: ShipmentType
  status: ShipmentStatus
  quantity: number
  created_at: string
  shipped_at: string | null
  delivered_at: string | null
}

export interface Operation {
  id: number
  product_id: number
  product_sku: string | null
  product_name: string | null
  warehouse_from_id: number | null
  warehouse_to_id: number | null
  operation_type: string
  quantity: number
  comment: string | null
  created_at: string
}
