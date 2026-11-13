import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { getMovements, getProducts, getWarehouses, createMovement, confirmMovement } from '../api/endpoints'
import type { Movement } from '../api/types'
import { ArrowRight, CheckCircle } from 'lucide-react'
import clsx from 'clsx'

const STATUS_LABELS: Record<string, string> = {
  pending: 'Ожидает',
  in_transit: 'В пути',
  completed: 'Принято',
  cancelled: 'Отменено',
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-50 text-yellow-700',
  in_transit: 'bg-blue-50 text-blue-700',
  completed: 'bg-green-50 text-green-600',
  cancelled: 'bg-gray-100 text-gray-500',
}

export default function MovementsPage() {
  const qc = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState({ product_id: '', warehouse_from_id: '', warehouse_to_id: '', quantity: '' })

  const { data: movements = [] } = useQuery({
    queryKey: ['movements'],
    queryFn: () => getMovements().then((r) => r.data),
  })
  const { data: products = [] } = useQuery({ queryKey: ['products'], queryFn: () => getProducts().then((r) => r.data) })
  const { data: warehouses = [] } = useQuery({ queryKey: ['warehouses'], queryFn: () => getWarehouses().then((r) => r.data) })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['movements'] })
    qc.invalidateQueries({ queryKey: ['stock'] })
    qc.invalidateQueries({ queryKey: ['operations'] })
  }

  const createMut = useMutation({
    mutationFn: () => createMovement({
      product_id: Number(form.product_id),
      warehouse_from_id: Number(form.warehouse_from_id),
      warehouse_to_id: Number(form.warehouse_to_id),
      quantity: Number(form.quantity),
    }),
    onSuccess: () => { toast.success('Перемещение создано, товар в пути'); invalidate(); setShowModal(false) },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Ошибка'),
  })

  const confirmMut = useMutation({
    mutationFn: (id: number) => confirmMovement(id),
    onSuccess: () => { toast.success('Приёмка подтверждена'); invalidate() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Ошибка'),
  })

  const whName = (id: number) => warehouses.find((w) => w.id === id)?.name ?? `#${id}`
  const prodName = (id: number) => {
    const p = products.find((p) => p.id === id)
    return p ? `${p.sku} ${p.name}` : `#${id}`
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Перемещения между ФФ</h2>
          <p className="text-gray-500 text-sm mt-0.5">Товар в пути между складами</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>
          + Создать перемещение
        </button>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left font-medium text-gray-500">ID</th>
              <th className="px-6 py-3 text-left font-medium text-gray-500">Товар</th>
              <th className="px-6 py-3 text-left font-medium text-gray-500">Маршрут</th>
              <th className="px-6 py-3 text-center font-medium text-gray-500">Кол-во</th>
              <th className="px-6 py-3 text-center font-medium text-gray-500">Статус</th>
              <th className="px-6 py-3 text-left font-medium text-gray-500">Создано</th>
              <th className="px-6 py-3 text-right font-medium text-gray-500">Действие</th>
            </tr>
          </thead>
          <tbody>
            {movements.map((m) => (
              <tr key={m.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="px-6 py-4 text-gray-400">#{m.id}</td>
                <td className="px-6 py-4 font-medium">{prodName(m.product_id)}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2 text-gray-600">
                    <span>{whName(m.warehouse_from_id)}</span>
                    <ArrowRight size={14} className="text-gray-400" />
                    <span>{whName(m.warehouse_to_id)}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-center font-semibold">{m.quantity}</td>
                <td className="px-6 py-4 text-center">
                  <span className={`badge ${STATUS_COLORS[m.status]}`}>
                    {STATUS_LABELS[m.status]}
                  </span>
                </td>
                <td className="px-6 py-4 text-gray-500">
                  {new Date(m.created_at).toLocaleString('ru')}
                </td>
                <td className="px-6 py-4 text-right">
                  {m.status === 'in_transit' && (
                    <button
                      className="btn-primary btn-sm flex items-center gap-1 ml-auto"
                      onClick={() => confirmMut.mutate(m.id)}
                      disabled={confirmMut.isPending}
                    >
                      <CheckCircle size={14} />
                      Подтвердить приёмку
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {movements.length === 0 && (
          <div className="text-center py-12 text-gray-400">Перемещений пока нет</div>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="card w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Создать перемещение</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Товар</label>
                <select className="input" value={form.product_id} onChange={(e) => setForm({ ...form, product_id: e.target.value })}>
                  <option value="">— выберите —</option>
                  {products.map((p) => <option key={p.id} value={p.id}>{p.sku} — {p.name}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Откуда</label>
                  <select className="input" value={form.warehouse_from_id} onChange={(e) => setForm({ ...form, warehouse_from_id: e.target.value })}>
                    <option value="">— склад —</option>
                    {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Куда</label>
                  <select className="input" value={form.warehouse_to_id} onChange={(e) => setForm({ ...form, warehouse_to_id: e.target.value })}>
                    <option value="">— склад —</option>
                    {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Количество</label>
                <input type="number" min={1} className="input" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                className="btn-primary flex-1"
                disabled={!form.product_id || !form.warehouse_from_id || !form.warehouse_to_id || !form.quantity || createMut.isPending}
                onClick={() => createMut.mutate()}
              >
                {createMut.isPending ? 'Создание...' : 'Создать'}
              </button>
              <button className="btn-secondary" onClick={() => setShowModal(false)}>Отмена</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
