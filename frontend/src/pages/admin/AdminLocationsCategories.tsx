import { useEffect, useState } from 'react'
import { apiFetch } from '../../lib/apiClient'

type Named = { id: string; name: string; active: boolean }

// Locations and categories are both tiny master-data lists with
// identical shape and rules, so one generic list component drives both
// halves of this page instead of writing the same thing twice.
function NamedList({ title, endpoint }: { title: string; endpoint: string }) {
  const [rows, setRows] = useState<Named[]>([])
  const [newName, setNewName] = useState('')
  const [error, setError] = useState<string | null>(null)

  // Admin management screen needs to see BOTH active and deactivated
  // entries (so old categories can still be reviewed/reactivated) -
  // every other part of the app only ever asks for active=true.
  function load() {
    Promise.all([apiFetch(`${endpoint}?active=true`), apiFetch(`${endpoint}?active=false`)])
      .then(([active, inactive]) => setRows([...active, ...inactive]))
  }
  useEffect(load, [endpoint])

  async function add() {
    if (!newName.trim()) return
    try {
      await apiFetch(endpoint, { method: 'POST', body: JSON.stringify({ name: newName.trim() }) })
      setNewName('')
      setError(null)
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not add.')
    }
  }

  async function toggleActive(row: Named) {
    await apiFetch(`${endpoint}/${row.id}`, { method: 'PATCH', body: JSON.stringify({ active: !row.active }) })
    load()
  }
  async function remove(row: Named) {
    if (!confirm(`Permanently delete "${row.name}"? This can't be undone, and only works if no items use it.`)) return
    try {
      await apiFetch(`${endpoint}/${row.id}`, { method: 'DELETE' })
      load()
    } catch (e) {
      // Most likely failure: items still reference this category - the
      // backend's message already explains that clearly, just show it.
      setError(e instanceof Error ? e.message : 'Could not delete.')
    }
  }
  return (
    <div className="flex-1">
      <h3 className="font-heading text-lg mb-3">{title}</h3>
      <div className="bg-white/60 border border-cream-dark rounded-lg divide-y divide-cream-dark mb-3">
        {rows.map((row) => (
          <div key={row.id} className="flex items-center justify-between px-3 py-2 text-sm">
            <span className={row.active ? '' : 'text-ink-soft line-through'}>{row.name}</span>
            <span className="flex gap-3">
              <button onClick={() => toggleActive(row)} className="text-accent">
                {row.active ? 'Deactivate' : 'Reactivate'}
              </button>
              <button onClick={() => remove(row)} className="text-status-critical">Delete</button>
            </span>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder={`New ${title.toLowerCase()}`}
          className="flex-1 border border-cream-dark rounded px-3 py-1.5 bg-white text-sm" />
        <button onClick={add} className="bg-accent text-white rounded px-3 text-sm">Add</button>
      </div>
      {error && <p className="text-status-critical text-sm mt-2">{error}</p>}
    </div>
  )
}

export function AdminLocationsCategories() {
  return (
    <div className="flex flex-col sm:flex-row gap-8">
      <NamedList title="Locations" endpoint="/api/v1/locations" />
      <NamedList title="Categories" endpoint="/api/v1/categories" />
    </div>
  )
}