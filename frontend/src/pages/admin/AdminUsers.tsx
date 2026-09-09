import { useEffect, useState, FormEvent } from 'react'
import { apiFetch } from '../../lib/apiClient'

type User = { id: string; name: string; email: string; role: string; active: boolean }
const ROLES = ['kitchen_staff', 'manager', 'admin']

export function AdminUsers() {
  const [users, setUsers] = useState<User[]>([])
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [newUser, setNewUser] = useState({ name: '', email: '', password: '', role: 'kitchen_staff' })
  const [createMessage, setCreateMessage] = useState<string | null>(null)

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

  async function createUser(e: FormEvent) {
    e.preventDefault()
    setCreating(true)
    setCreateMessage(null)
    try {
      await apiFetch('/api/v1/users', { method: 'POST', body: JSON.stringify(newUser) })
      setCreateMessage(`${newUser.name} can now log in.`)
      setNewUser({ name: '', email: '', password: '', role: 'kitchen_staff' })
      load()
    } catch (e) {
      setCreateMessage(e instanceof Error ? e.message : 'Could not create user.')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div>
      <form onSubmit={createUser} className="bg-white/60 border border-cream-dark rounded-lg p-4 mb-6">
        <p className="font-heading text-base mb-3">Add a new user</p>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-2">
          <input required placeholder="Full name" value={newUser.name}
            onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
            className="border border-cream-dark rounded px-3 py-1.5 bg-white text-sm" />
          <input required type="email" placeholder="Email" value={newUser.email}
            onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
            className="border border-cream-dark rounded px-3 py-1.5 bg-white text-sm" />
          <input required type="password" placeholder="Temporary password" value={newUser.password}
            onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
            className="border border-cream-dark rounded px-3 py-1.5 bg-white text-sm" />
          <select value={newUser.role} onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
            className="border border-cream-dark rounded px-3 py-1.5 bg-white text-sm">
            {ROLES.map((r) => <option key={r} value={r}>{r.replace('_', ' ')}</option>)}
          </select>
        </div>
        <button disabled={creating} type="submit" className="mt-3 bg-accent text-white rounded px-4 py-1.5 text-sm disabled:opacity-50">
          {creating ? 'Creating…' : 'Add user'}
        </button>
        {createMessage && <p className="text-sm mt-2 text-ink-soft">{createMessage}</p>}
      </form>

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