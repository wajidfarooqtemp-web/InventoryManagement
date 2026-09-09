import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { Layout } from './components/Layout'
import { Login } from './pages/Login'
import { Overview } from './pages/Overview'
import { Inventory } from './pages/Inventory'
import { Activity } from './pages/Activity'
import { PurchaseList } from './pages/PurchaseList'
import { AdminLayout } from './pages/admin/AdminLayout'
import { AdminItems } from './pages/admin/AdminItems'
import { AdminLocationsCategories } from './pages/admin/AdminLocationsCategories'
import { AdminUsers } from './pages/admin/AdminUsers'
import { AdminDataConfirmation } from './pages/admin/AdminDataConfirmation'

// Stand-ins for routes the Layout already links to, so navigation
// doesn't dead-end while Inventory/Activity/Purchase List/Admin get
// built out for real in Phases 8-9.
function ComingSoon({ title }: { title: string }) {
  return <p className="text-ink-soft">{title} — coming in a later phase.</p>
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<Overview />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/activity" element={<Activity />} />
            <Route path="/purchase-list" element={<PurchaseList />} />
            <Route path="/admin" element={<AdminLayout />}>
  <Route index element={<AdminItems />} />
  <Route path="items" element={<AdminItems />} />
  <Route path="locations" element={<AdminLocationsCategories />} />
  <Route path="users" element={<AdminUsers />} />
  <Route path="data-confirmation" element={<AdminDataConfirmation />} />
</Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App