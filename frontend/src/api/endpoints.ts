import api from './client'
import type { Movement, Operation, Product, Shipment, StockItem, Warehouse } from './types'

// ── Auth ────────────────────────────────────────────────────────────────────
export const login = (username: string, password: string) =>
  api.post<{ access_token: string }>('/auth/login', { username, password })

// ── Warehouses ──────────────────────────────────────────────────────────────
export const getWarehouses = (includeDeleted = false) =>
  api.get<Warehouse[]>(`/warehouses?include_deleted=${includeDeleted}`)

export const createWarehouse = (name: string) =>
  api.post<Warehouse>('/warehouses', { name })

export const renameWarehouse = (id: number, name: string) =>
  api.patch<Warehouse>(`/warehouses/${id}`, { name })

export const deleteWarehouse = (id: number) =>
  api.delete<Warehouse>(`/warehouses/${id}`)

// ── Stock ────────────────────────────────────────────────────────────────────
export const getStock = () => api.get<StockItem[]>('/stock')

export const getProducts = () => api.get<Product[]>('/stock/products')

export const receiveStock = (product_id: number, warehouse_id: number, quantity: number) =>
  api.post('/stock/receive', { product_id, warehouse_id, quantity })

export const getOperations = (params?: { product_id?: number; warehouse_id?: number }) =>
  api.get<Operation[]>('/stock/operations', { params })

// ── Movements ───────────────────────────────────────────────────────────────
export const getMovements = () => api.get<Movement[]>('/movements')

export const createMovement = (data: {
  product_id: number
  warehouse_from_id: number
  warehouse_to_id: number
  quantity: number
}) => api.post<Movement>('/movements', data)

export const confirmMovement = (id: number) =>
  api.post<Movement>(`/movements/${id}/confirm`)

// ── Shipments ────────────────────────────────────────────────────────────────
export const getShipments = () => api.get<Shipment[]>('/shipments')

export const reserveFBS = (product_id: number, warehouse_id: number, quantity: number) =>
  api.post<Shipment>('/shipments/fbs/reserve', { product_id, warehouse_id, quantity })

export const shipFBS = (id: number) => api.post<Shipment>(`/shipments/fbs/${id}/ship`)

export const cancelFBS = (id: number) => api.post<Shipment>(`/shipments/fbs/${id}/cancel`)

export const shipFBO = (product_id: number, warehouse_id: number, quantity: number) =>
  api.post<Shipment>('/shipments/fbo/ship', { product_id, warehouse_id, quantity })

export const receiveFBO = (id: number) => api.post<Shipment>(`/shipments/fbo/${id}/receive`)
