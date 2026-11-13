import { useQuery } from '@tanstack/react-query'
import { getOperations, getProducts, getWarehouses } from '../api/endpoints'
import type { Operation } from '../api/types'

const OP_LABELS: Record<string, string> = {
  receipt: '📥 Приход',
  movement_out: '📤 Перемещение (отправка)',
  movement_in: '📥 Перемещение (приёмка)',
  reserve_fbs: '🔒 Резерв FBS',
  unreserve_fbs: '🔓 Снятие резерва FBS',
  ship_fbs: '🚚 FBS отправлено',
  ship_fbo: '📦 FBO отправлено',
  receive_fbo: '✅ FBO принято',
  cancel_shipment: '❌ Отмена отправки',
  warehouse_deleted: '🗑️ Склад удалён',
}

export default function HistoryPage() {
  const { data: operations = [], isLoading } = useQuery({
    queryKey: ['operations'],
    queryFn: () => getOperations().then((r) => r.data),
    refetchInterval: 15_000,
  })

  const { data: warehouses = [] } = useQuery({
    queryKey: ['warehouses', true],
    queryFn: () => getWarehouses(true).then((r) => r.data),
  })

  const whName = (id: number | null) => {
    if (!id) return '—'
    return warehouses.find((w) => w.id === id)?.name ?? `#${id}`
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">История операций</h2>
        <p className="text-gray-500 text-sm mt-0.5">
          Все движения товаров — приход, перемещения, резервы и отправки
        </p>
      </div>

      {isLoading ? (
        <div className="text-gray-400 text-center py-16">Загрузка...</div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Операция</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Товар</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Откуда</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Куда</th>
                <th className="px-6 py-3 text-center font-medium text-gray-500">Кол-во</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Комментарий</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Время</th>
              </tr>
            </thead>
            <tbody>
              {operations.map((op) => (
                <tr key={op.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-6 py-3 whitespace-nowrap">
                    {OP_LABELS[op.operation_type] ?? op.operation_type}
                  </td>
                  <td className="px-6 py-3">
                    <span className="font-medium">{op.product_sku}</span>
                    <span className="text-gray-400 ml-1 text-xs">{op.product_name}</span>
                  </td>
                  <td className="px-6 py-3 text-gray-600">{whName(op.warehouse_from_id)}</td>
                  <td className="px-6 py-3 text-gray-600">{whName(op.warehouse_to_id)}</td>
                  <td className="px-6 py-3 text-center font-semibold">{op.quantity}</td>
                  <td className="px-6 py-3 text-gray-400 text-xs">{op.comment ?? '—'}</td>
                  <td className="px-6 py-3 text-gray-500 whitespace-nowrap">
                    {new Date(op.created_at).toLocaleString('ru')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {operations.length === 0 && (
            <div className="text-center py-12 text-gray-400">История пуста</div>
          )}
        </div>
      )}
    </div>
  )
}
