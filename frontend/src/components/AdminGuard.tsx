import { useAuth } from '../contexts/AuthContext'

// UX convenience only, same caveat as ProtectedRoute - the real
// enforcement is the backend's require_role("admin") on every request.
export function AdminGuard({ children }: { children: React.ReactNode }) {
  const { profile } = useAuth()
  if (profile?.role !== 'admin') {
    return <p className="text-ink-soft">You need admin access to view this page.</p>
  }
  return <>{children}</>
}