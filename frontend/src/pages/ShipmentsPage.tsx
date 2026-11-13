import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import {
  getShipments, getProducts, getWarehouses,
  reserveFBS, shipFBS, cancelFBS, shipFBO, receiveFBO
} from '../api/endpoints'
import type { Shipment } from '../api/types'
import { Send, Package, XCircle, CheckCircle } from 'lucide-react'

const STATUS_LABELS: Record<string, string> = {
  reserved: 'Зарезервировано',
  shipped: 'В пути',
  delivered: 'Доставлено / Принято',
  cancelled: 'Отменено',
}

const STATUS_COLORS: Record<string, string> = {
  reserved: 'bg-amber-50 text-amber-700',
  shipped: 'bg-blue-50 text-blue-700',
  delivered: 'bg-green-50 text-green-600',
  cancelled: 'bg-gray-100 text-gray-500',
}

export default function ShipmentsPage() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<'fbs' | 'fbo'>('fbs')
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState({ product_id: '', warehouse_id: '', quantity: '' })

  const { data: shipments = [] } = useQuery({
    queryKey: ['shipments'],
    queryFn: () => getShipments().then((r) => r.data),
  })
  const { data: products = [] } = useQuery({ queryKey: ['products'], queryFn: () => getProducts().then((r) => r.data) })
  const { data: warehouses = [] } = useQuery({ queryKey: ['warehouses'], queryFn: () => getWarehouses().then((r) => r.data) })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['shipments'] })
    qc.invalidateQueries({ queryKey: ['stock'] })
    qc.invalidateQueries({ queryKey: ['operations'] })
  }

  const reserveMut = useMutation({
    mutationFn: () => reserveFBS(Number(form.product_id), Number(form.warehouse_id), Number(form.quantity)),
    onSuccess: () => { toast.success('FBS зарезервировано'); invalidate(); setShowModal(false) },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Нехватка товара'),
  })

  const shipFBOMut = useMutation({
    mutationFn: () => shipFBO(Number(form.product_id), Number(form.warehouse_id), Number(form.quantity)),
    onSuccess: () => { toast.success('FBO отправлено на маркетплейс'); invalidate(); setShowModal(false) },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Нехватка товара'),
  })

  const shipMut = useMutation({
    mutationFn: (id: number) => shipFBS(id),
    onSuccess: () => { toast.success('FBS отправлено клиенту'); invalidate() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Ошибка'),
  })

  const cancelMut = useMutation({
    mutationFn: (id: number) => cancelFBS(id),
    onSuccess: () => { toast.success('Резерв отменён'); invalidate() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Ошибка'),
  })

  const receiveMut = useMutation({
    mutationFn: (id: number) => receiveFBO(id),
    onSuccess: () => { toast.success('FBO принято маркетплейсом'); invalidate() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Ошибка'),
  })

  const whName = (id: number) => warehouses.find((w) => w.id === id)?.name ?? `#${id}`
  const prodName = (id: number) => {
    const p = products.find((p) => p.id === id)
    return p ? `${p.sku} ${p.name}` : `#${id}`
  }

  const filtered = shipments.filter((s) => s.shipment_type === tab)

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Отправки FBS / FBO</h2>
          <p className="text-gray-500 text-sm mt-0.5">Управление отправками на маркетплейс и клиентам</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>
          + Новая отправка
        </button>
      </div>

      {/* Вкладки */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-lg w-fit mb-6">
        {(['fbs', 'fbo'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
              tab === t ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.toUpperCase()}
            <span className="ml-2 text-xs opacity-60">
              {t === 'fbs' ? '→ клиенту' : '→ маркетплейс'}
            </span>
          </button>
        ))}
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left font-medium text-gray-500">ID</th>
              <th className="px-6 py-3 text-left font-medium text-gray-500">Товар</th>
              <th className="px-6 py-3 text-left font-medium text-gray-500">Склад ФФ</th>
              <th className="px-6 py-3 text-center font-medium text-gray-500">Кол-во</th>
              <th className="px-6 py-3 text-center font-medium text-gray-500">Статус</th>
              <th className="px-6 py-3 text-left font-medium text-gray-500">Создано</th>
              <th className="px-6 py-3 text-right font-medium text-gray-500">Действия</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((s) => (
              <tr key={s.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="px-6 py-4 text-gray-400">#{s.id}</td>
                <td className="px-6 py-4 font-medium">{prodName(s.product_id)}</td>
                <td className="px-6 py-4 text-gray-600">{whName(s.warehouse_id)}</td>
                <td className="px-6 py-4 text-center font-semibold">{s.quantity}</td>
                <td className="px-6 py-4 text-center">
                  <span className={`badge ${STATUS_COLORS[s.status]}`}>
                    {STATUS_LABELS[s.status]}
                  </span>
                </td>
                <td className="px-6 py-4 text-gray-500">
                  {new Date(s.created_at).toLocaleString('ru')}
                </td>
                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    {/* FBS: зарезервировано → отправить или отменить */}
                    {s.shipment_type === 'fbs' && s.status === 'reserved' && (
                      <>
                        <button className="btn-primary btn-sm flex items-center gap-1" onClick={() => shipMut.mutate(s.id)}>
                          <Send size={12} /> Отправить
                        </button>
                        <button className="btn-danger btn-sm flex items-center gap-1" onClick={() => cancelMut.mutate(s.id)}>
                          <XCircle size={12} /> Отмена
                        </button>
                      </>
                    )}
                    {/* FBO: в пути → подтвердить приёмку */}
                    {s.shipment_type === 'fbo' && s.status === 'shipped' && (
                      <button className="btn-primary btn-sm flex items-center gap-1" onClick={() => receiveMut.mutate(s.id)}>
                        <CheckCircle size={12} /> Принято маркетплейсом
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center py-12 text-gray-400">Нет отправок</div>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="card w-full max-w-md">
            <h3 className="text-lg font-semibold mb-1">Новая отправка</h3>
            <div className="flex gap-1 p-1 bg-gray-100 rounded-lg w-fit mb-4">
              {(['fbs', 'fbo'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${tab === t ? 'bg-white shadow' : 'text-gray-500'}`}
                >
                  {t.toUpperCase()}
                </button>
              ))}
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Товар</label>
                <select className="input" value={form.product_id} onChange={(e) => setForm({ ...form, product_id: e.target.value })}>
                  <option value="">— выберите —</option>
                  {products.map((p) => <option key={p.id} value={p.id}>{p.sku} — {p.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Склад ФФ</label>
                <select className="input" value={form.warehouse_id} onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })}>
                  <option value="">— выберите —</option>
                  {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Количество</label>
                <input type="number" min={1} className="input" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                className="btn-primary flex-1"
                disabled={!form.product_id || !form.warehouse_id || !form.quantity}
                onClick={() => tab === 'fbs' ? reserveMut.mutate() : shipFBOMut.mutate()}
              >
                {tab === 'fbs' ? 'Зарезервировать FBS' : 'Отправить FBO'}
              </button>
              <button className="btn-secondary" onClick={() => setShowModal(false)}>Отмена</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
