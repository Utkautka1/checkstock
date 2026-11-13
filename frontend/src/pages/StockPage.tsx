import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { getStock, getProducts, getWarehouses, receiveStock } from '../api/endpoints'
import type { StockItem } from '../api/types'
import { Package, TrendingDown, AlertTriangle } from 'lucide-react'

function StockBadge({ value, type }: { value: number; type: 'physical' | 'available' | 'reserved' }) {
  const styles = {
    physical: 'bg-blue-50 text-blue-700',
    available: value > 0 ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600',
    reserved: value > 0 ? 'bg-amber-50 text-amber-700' : 'bg-gray-50 text-gray-400',
  }
  return (
    <span className={`badge ${styles[type]} font-semibold text-sm px-3 py-1`}>
      {value}
    </span>
  )
}

export default function StockPage() {
  const qc = useQueryClient()
  const [showReceiveModal, setShowReceiveModal] = useState(false)
  const [form, setForm] = useState({ product_id: '', warehouse_id: '', quantity: '' })

  const { data: stock = [], isLoading } = useQuery({
    queryKey: ['stock'],
    queryFn: () => getStock().then((r) => r.data),
  })

  const { data: products = [] } = useQuery({
    queryKey: ['products'],
    queryFn: () => getProducts().then((r) => r.data),
  })

  const { data: warehouses = [] } = useQuery({
    queryKey: ['warehouses'],
    queryFn: () => getWarehouses().then((r) => r.data),
  })

  const receive = useMutation({
    mutationFn: () =>
      receiveStock(Number(form.product_id), Number(form.warehouse_id), Number(form.quantity)),
    onSuccess: () => {
      toast.success('Приход оформлен')
      qc.invalidateQueries({ queryKey: ['stock'] })
      qc.invalidateQueries({ queryKey: ['operations'] })
      setShowReceiveModal(false)
      setForm({ product_id: '', warehouse_id: '', quantity: '' })
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Ошибка'),
  })

  // Группируем остатки по товарам
  const grouped = stock.reduce<Record<string, StockItem[]>>((acc, item) => {
    const key = item.product_sku
    if (!acc[key]) acc[key] = []
    acc[key].push(item)
    return acc
  }, {})

  // Суммарный доступный остаток по товару (для отображения)
  const totalAvailable = (items: StockItem[]) => items.reduce((s, i) => s + i.quantity_available, 0)

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Остатки товаров</h2>
          <p className="text-gray-500 text-sm mt-0.5">
            Физически на складе, доступно для отправки, в резерве FBS
          </p>
        </div>
        <button className="btn-primary" onClick={() => setShowReceiveModal(true)}>
          + Оформить приход
        </button>
      </div>

      {isLoading ? (
        <div className="text-gray-400 text-center py-16">Загрузка...</div>
      ) : (
        <div className="space-y-4">
          {Object.entries(grouped).map(([sku, items]) => {
            const total = totalAvailable(items)
            return (
              <div key={sku} className="card p-0 overflow-hidden">
                {/* Заголовок товара */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50">
                  <div className="flex items-center gap-3">
                    <Package size={18} className="text-gray-400" />
                    <div>
                      <span className="font-semibold text-gray-900">{items[0].product_name}</span>
                      <span className="ml-2 text-sm text-gray-400">{sku}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    {total === 0 && (
                      <span className="flex items-center gap-1 text-red-500">
                        <AlertTriangle size={14} />
                        Нет доступного остатка
                      </span>
                    )}
                    <span>Доступно всего: <strong className="text-gray-800">{total}</strong></span>
                  </div>
                </div>

                {/* Строки по складам */}
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-xs text-gray-400 uppercase border-b border-gray-100">
                      <th className="px-6 py-2 text-left font-medium">Склад ФФ</th>
                      <th className="px-6 py-2 text-center font-medium">Физически</th>
                      <th className="px-6 py-2 text-center font-medium">Доступно</th>
                      <th className="px-6 py-2 text-center font-medium">Резерв FBS</th>
                      <th className="px-6 py-2 text-center font-medium">Статус склада</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item) => (
                      <tr key={item.warehouse_id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="px-6 py-3 font-medium">
                          {item.warehouse_name}
                          {!item.warehouse_active && (
                            <span className="ml-2 text-xs text-red-400">(удалён)</span>
                          )}
                        </td>
                        <td className="px-6 py-3 text-center">
                          <StockBadge value={item.quantity_physical} type="physical" />
                        </td>
                        <td className="px-6 py-3 text-center">
                          <StockBadge value={item.quantity_available} type="available" />
                        </td>
                        <td className="px-6 py-3 text-center">
                          <StockBadge value={item.quantity_reserved} type="reserved" />
                        </td>
                        <td className="px-6 py-3 text-center">
                          {item.warehouse_active ? (
                            <span className="badge bg-green-50 text-green-600">Активен</span>
                          ) : (
                            <span className="badge bg-red-50 text-red-500">Удалён</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          })}

          {Object.keys(grouped).length === 0 && (
            <div className="text-center py-16 text-gray-400">
              <TrendingDown size={40} className="mx-auto mb-3 opacity-30" />
              <p>Остатков пока нет. Оформите приход товара.</p>
            </div>
          )}
        </div>
      )}

      {/* Модал прихода */}
      {showReceiveModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="card w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Приход товара</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Товар</label>
                <select
                  className="input"
                  value={form.product_id}
                  onChange={(e) => setForm({ ...form, product_id: e.target.value })}
                >
                  <option value="">— выберите товар —</option>
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.sku} — {p.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Склад ФФ</label>
                <select
                  className="input"
                  value={form.warehouse_id}
                  onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })}
                >
                  <option value="">— выберите склад —</option>
                  {warehouses.map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Количество</label>
                <input
                  type="number"
                  min={1}
                  className="input"
                  value={form.quantity}
                  onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                className="btn-primary flex-1"
                disabled={!form.product_id || !form.warehouse_id || !form.quantity || receive.isPending}
                onClick={() => receive.mutate()}
              >
                {receive.isPending ? 'Оформление...' : 'Оформить приход'}
              </button>
              <button className="btn-secondary" onClick={() => setShowReceiveModal(false)}>
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
