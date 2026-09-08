import { Link, Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { ChinarMark } from './ChinarMark'

// Shared shell for every logged-in screen. Role-based nav visibility here
// is a UX convenience only - the backend enforces the real permission on
// every request regardless of what links are shown (Section 19).
export function Layout() {
  const { profile, signOut } = useAuth()
  const isManagerOrAdmin = profile?.role === 'manager' || profile?.role === 'admin'
  const isAdmin = profile?.role === 'admin'

  return (
    <div className="min-h-screen bg-cream text-ink font-body">
      <header className="border-b border-cream-dark px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <ChinarMark className="w-6 h-6 text-accent" />
          <span className="font-heading text-lg tracking-wide">Inventory</span>
        </Link>

        <nav className="flex items-center gap-6 text-sm">
          <Link to="/" className="hover:text-accent">Overview</Link>
          <Link to="/inventory" className="hover:text-accent">Inventory</Link>
          <Link to="/activity" className="hover:text-accent">Activity</Link>
          {isManagerOrAdmin && <Link to="/purchase-list" className="hover:text-accent">Purchase List</Link>}
          {isAdmin && <Link to="/admin" className="hover:text-accent">Admin</Link>}
        </nav>

        <div className="flex items-center gap-3 text-sm">
          <span className="text-ink-soft">{profile?.name} · {profile?.role.replace('_', ' ')}</span>
          <button onClick={signOut} className="text-accent hover:underline">Log out</button>
        </div>
      </header>

      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}