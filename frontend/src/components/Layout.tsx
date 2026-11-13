import { NavLink, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { BarChart3, Building2, History, LogOut, Package, Send } from 'lucide-react'
import clsx from 'clsx'

const NAV = [
  { to: '/stock', icon: BarChart3, label: 'Остатки' },
  { to: '/warehouses', icon: Building2, label: 'Склады ФФ' },
  { to: '/movements', icon: Package, label: 'Перемещения' },
  { to: '/shipments', icon: Send, label: 'Отправки' },
  { to: '/history', icon: History, label: 'История' },
]

export default function Layout() {
  const { username, logout } = useAuthStore()

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col">
        <div className="px-6 py-5 border-b border-gray-200">
          <h1 className="text-xl font-bold text-sky-600">CheckStock</h1>
          <p className="text-xs text-gray-500 mt-0.5">Где сейчас товар?</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-sky-50 text-sky-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                )
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-3 py-4 border-t border-gray-200">
          <div className="flex items-center justify-between px-3">
            <span className="text-sm text-gray-600">{username}</span>
            <button
              onClick={logout}
              className="text-gray-400 hover:text-red-500 transition-colors"
              title="Выйти"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
