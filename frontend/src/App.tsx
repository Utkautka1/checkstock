import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from './store/auth'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import StockPage from './pages/StockPage'
import WarehousesPage from './pages/WarehousesPage'
import MovementsPage from './pages/MovementsPage'
import ShipmentsPage from './pages/ShipmentsPage'
import HistoryPage from './pages/HistoryPage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/stock" replace />} />
          <Route path="stock" element={<StockPage />} />
          <Route path="warehouses" element={<WarehousesPage />} />
          <Route path="movements" element={<MovementsPage />} />
          <Route path="shipments" element={<ShipmentsPage />} />
          <Route path="history" element={<HistoryPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
