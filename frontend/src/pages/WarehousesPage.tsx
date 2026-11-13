import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { getWarehouses, createWarehouse, renameWarehouse, deleteWarehouse } from '../api/endpoints'
import { Building2, Pencil, Trash2 } from 'lucide-react'
import type { Warehouse } from '../api/types'

export default function WarehousesPage() {
  const qc = useQueryClient()
  const [showAdd, setShowAdd] = useState(false)
  const [newName, setNewName] = useState('')
  const [editId, setEditId] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [showDeleted, setShowDeleted] = useState(false)

  const { data: warehouses = [] } = useQuery({
    queryKey: ['warehouses', showDeleted],
    queryFn: () => getWarehouses(showDeleted).then((r) => r.data),
  })

  const invalidate = () => qc.invalidateQueries({ queryKey: ['warehouses'] })

  const addMut = useMutation({
    mutationFn: () => createWarehouse(newName),
    onSuccess: () => { toast.success('Склад создан'); invalidate(); setNewName(''); setShowAdd(false) },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Ошибка'),
  })

  const renameMut = useMutation({
    mutationFn: (id: number) => renameWarehouse(id, editName),
    onSuccess: () => { toast.success('Переименовано'); invalidate(); setEditId(null) },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Ошибка'),
  })

  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteWarehouse(id),
    onSuccess: () => { toast.success('Склад удалён (мягко — история сохранена)'); invalidate() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Ошибка'),
  })

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Склады фулфилмента</h2>
          <p className="text-gray-500 text-sm mt-0.5">Управление складами ФФ</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={showDeleted}
              onChange={(e) => setShowDeleted(e.target.checked)}
              className="rounded"
            />
            Показать удалённые
          </label>
          <button className="btn-primary" onClick={() => setShowAdd(true)}>
            + Добавить склад
          </button>
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left font-medium text-gray-500">Склад</th>
              <th className="px-6 py-3 text-left font-medium text-gray-500">Статус</th>
              <th className="px-6 py-3 text-left font-medium text-gray-500">Создан</th>
              <th className="px-6 py-3 text-left font-medium text-gray-500">Удалён</th>
              <th className="px-6 py-3 text-right font-medium text-gray-500">Действия</th>
            </tr>
          </thead>
          <tbody>
            {warehouses.map((wh) => (
              <tr key={wh.id} className={`border-b border-gray-100 ${!wh.is_active ? 'opacity-50' : ''}`}>
                <td className="px-6 py-4 font-medium">
                  <div className="flex items-center gap-2">
                    <Building2 size={16} className="text-gray-400" />
                    {editId === wh.id ? (
                      <input
                        className="input py-1"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        autoFocus
                      />
                    ) : (
                      wh.name
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  {wh.is_active ? (
                    <span className="badge bg-green-50 text-green-600">Активен</span>
                  ) : (
                    <span className="badge bg-red-50 text-red-500">Удалён</span>
                  )}
                </td>
                <td className="px-6 py-4 text-gray-500">
                  {new Date(wh.created_at).toLocaleDateString('ru')}
                </td>
                <td className="px-6 py-4 text-gray-500">
                  {wh.deleted_at ? new Date(wh.deleted_at).toLocaleDateString('ru') : '—'}
                </td>
                <td className="px-6 py-4 text-right">
                  {wh.is_active && (
                    <div className="flex items-center justify-end gap-2">
                      {editId === wh.id ? (
                        <>
                          <button
                            className="btn-primary btn-sm"
                            onClick={() => renameMut.mutate(wh.id)}
                          >
                            Сохранить
                          </button>
                          <button className="btn-secondary btn-sm" onClick={() => setEditId(null)}>
                            Отмена
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            className="btn-secondary btn-sm"
                            onClick={() => { setEditId(wh.id); setEditName(wh.name) }}
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            className="btn-danger btn-sm"
                            onClick={() => {
                              if (confirm(`Удалить склад "${wh.name}"? История и остатки сохранятся.`)) {
                                deleteMut.mutate(wh.id)
                              }
                            }}
                          >
                            <Trash2 size={14} />
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {warehouses.length === 0 && (
          <div className="text-center py-12 text-gray-400">Нет складов</div>
        )}
      </div>

      {/* Модал добавления */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="card w-full max-w-sm">
            <h3 className="text-lg font-semibold mb-4">Новый склад ФФ</h3>
            <input
              className="input"
              placeholder="Название склада"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addMut.mutate()}
              autoFocus
            />
            <div className="flex gap-3 mt-4">
              <button
                className="btn-primary flex-1"
                disabled={!newName.trim() || addMut.isPending}
                onClick={() => addMut.mutate()}
              >
                Создать
              </button>
              <button className="btn-secondary" onClick={() => { setShowAdd(false); setNewName('') }}>
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
