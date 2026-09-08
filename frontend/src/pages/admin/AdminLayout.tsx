import { NavLink, Outlet } from 'react-router-dom'
import { AdminGuard } from '../../components/AdminGuard'

const TABS = [
  { to: '/admin/items', label: 'Items' },
  { to: '/admin/locations', label: 'Locations & Categories' },
  { to: '/admin/users', label: 'Users' },
  { to: '/admin/data-confirmation', label: 'Data Confirmation' },
]

export function AdminLayout() {
  return (
    <AdminGuard>
      <div className="max-w-5xl mx-auto">
        <nav className="flex gap-4 border-b border-cream-dark mb-6 text-sm">
          {TABS.map((tab) => (
            <NavLink
              key={tab.to} to={tab.to}
              className={({ isActive }) =>
                `pb-3 border-b-2 ${isActive ? 'border-accent text-accent font-medium' : 'border-transparent text-ink-soft hover:text-ink'}`
              }
            >
              {tab.label}
            </NavLink>
          ))}
        </nav>
        <Outlet />
      </div>
    </AdminGuard>
  )
}