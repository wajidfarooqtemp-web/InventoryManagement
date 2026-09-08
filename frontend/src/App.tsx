import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { Layout } from './components/Layout'
import { Login } from './pages/Login'
import { Overview } from './pages/Overview'
import { Inventory } from './pages/Inventory'

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
            <Route path="/activity" element={<ComingSoon title="Activity" />} />
            <Route path="/purchase-list" element={<ComingSoon title="Purchase List" />} />
            <Route path="/admin" element={<ComingSoon title="Admin" />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App