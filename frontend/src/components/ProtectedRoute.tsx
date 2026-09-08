import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

// A UX convenience (redirect to login) - NOT the security boundary.
// The real enforcement happens in FastAPI on every request regardless.
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { profile, loading } = useAuth()

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-cream text-ink-soft">Loading…</div>
  if (!profile) return <Navigate to="/login" replace />

  return <>{children}</>
}