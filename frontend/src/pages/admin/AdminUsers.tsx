import { useEffect, useState } from 'react'
import { apiFetch } from '../../lib/apiClient'

type User = { id: string; name: string; email: string; role: string; active: boolean }
const ROLES = ['kitchen_staff', 'manager', 'admin']

export function AdminUsers() {
  const [users, setUsers] = useState<User[]>([])
  const [error, setError] = useState<string | null>(null)

  function load() {
    apiFetch('/api/v1/users').then(setUsers)
  }
  useEffect(load, [])

  async function changeRole(user: User, role: string) {
    try {
      await apiFetch(`/api/v1/users/${user.id}/role`, { method: 'PATCH', body: JSON.stringify({ role }) })
      setError(null)
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not change role.')
    }
  }

  async function toggleActive(user: User) {
    try {
      await apiFetch(`/api/v1/users/${user.id}/active`, { method: 'PATCH', body: JSON.stringify({ active: !user.active }) })
      setError(null)
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not change access.')
    }
  }

  return (
    <div>
      {error && <p className="text-status-critical text-sm mb-3">{error}</p>}
      <div className="bg-white/60 border border-cream-dark rounded-lg divide-y divide-cream-dark">
        {users.map((user) => (
          <div key={user.id} className="flex items-center justify-between px-4 py-3 text-sm">
            <div>
              <p className="font-medium">{user.name}</p>
              <p className="text-ink-soft">{user.email}</p>
            </div>
            <div className="flex items-center gap-3">
              <select value={user.role} onChange={(e) => changeRole(user, e.target.value)}
                className="border border-cream-dark rounded px-2 py-1 bg-white text-sm">
                {ROLES.map((r) => <option key={r} value={r}>{r.replace('_', ' ')}</option>)}
              </select>
              <button onClick={() => toggleActive(user)} className={user.active ? 'text-status-critical' : 'text-status-good'}>
                {user.active ? 'Deactivate' : 'Reactivate'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}