import { useEffect, useState } from 'react'
import { apiFetch, apiUpload } from '../../lib/apiClient'

type Item = {
  id: string
  name: string
  location_id: string
  location_name: string
  category_id: string
  category_name: string
  unit: string
  current_stock: number
  reorder_level: number | null
  critical_level: number | null
  active: boolean
}
type Option = { id: string; name: string }

export function AdminItems() {
  const [items, setItems] = useState<Item[]>([])
  const [locations, setLocations] = useState<Option[]>([])
  const [categories, setCategories] = useState<Option[]>([])
  const [editingId, setEditingId] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  function loadItems() {
    apiFetch('/api/v1/inventory?active=true').then(setItems)
  }

  useEffect(() => {
    loadItems()
    apiFetch('/api/v1/locations').then(setLocations)
    apiFetch('/api/v1/categories').then(setCategories)
  }, [])

  // A single PATCH used for every field on the edit row - thresholds,
  // category, location, unit. current_stock is deliberately never part
  // of this form - it can only change through a real stock movement.
  async function saveItem(item: Item) {
    try {
      await apiFetch(`/api/v1/inventory/${item.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          location_id: item.location_id,
          category_id: item.category_id,
          unit: item.unit,
          reorder_level: item.reorder_level,
          critical_level: item.critical_level,
        }),
      })
      setMessage(`${item.name} updated.`)
      setEditingId(null)
      loadItems()
    } catch {
      setMessage('Could not save changes. Please try again.')
    }
  }
  async function uploadImage(item: Item, file: File) {
    try {
      await apiUpload(`/api/v1/inventory/${item.id}/image`, file)
      setMessage(`${item.name} photo updated.`)
      loadItems()
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Could not upload image.')
    }
  }
  async function deactivateItem(item: Item) {
    if (!confirm(`Deactivate ${item.name}? It will be hidden from normal inventory views but its history is kept.`)) return
    await apiFetch(`/api/v1/inventory/${item.id}/deactivate`, { method: 'PATCH' })
    loadItems()
  }

  return (
    <div>
      {message && <p className="text-sm text-status-good mb-3">{message}</p>}
      <div className="bg-white/60 border border-cream-dark rounded-lg divide-y divide-cream-dark">
        {items.map((item) => (
          <div key={item.id} className="p-4">
            {editingId === item.id ? (
              <EditRow
                item={item} locations={locations} categories={categories}
                onCancel={() => setEditingId(null)} onSave={saveItem}
              />
            ) : (
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{item.name}</p>
                  <p className="text-sm text-ink-soft">
                    {item.location_name} · {item.category_name} · {item.current_stock} {item.unit} ·
                    reorder at {item.reorder_level ?? '—'}, critical at {item.critical_level ?? '—'}
                  </p>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <label className="text-accent cursor-pointer">
                    Photo
                    <input
                      type="file" accept="image/jpeg,image/png,image/webp" className="hidden"
                      onChange={(e) => e.target.files?.[0] && uploadImage(item, e.target.files[0])}
                    />
                  </label>
                  <button onClick={() => setEditingId(item.id)} className="text-accent">Edit</button>
                  <button onClick={() => deactivateItem(item)} className="text-status-critical">Deactivate</button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function EditRow({
  item, locations, categories, onCancel, onSave,
}: { item: Item; locations: Option[]; categories: Option[]; onCancel: () => void; onSave: (i: Item) => void }) {
  const [draft, setDraft] = useState(item)
  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 items-end">
      <div>
        <label className="block text-xs text-ink-soft mb-1">Location</label>
        <select value={draft.location_id} onChange={(e) => setDraft({ ...draft, location_id: e.target.value })}
          className="w-full border border-cream-dark rounded px-2 py-1.5 bg-white text-sm">
          {locations.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
        </select>
      </div>
      <div>
        <label className="block text-xs text-ink-soft mb-1">Category</label>
        <select value={draft.category_id} onChange={(e) => setDraft({ ...draft, category_id: e.target.value })}
          className="w-full border border-cream-dark rounded px-2 py-1.5 bg-white text-sm">
          {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>
      <div>
        <label className="block text-xs text-ink-soft mb-1">Unit</label>
        <input value={draft.unit} onChange={(e) => setDraft({ ...draft, unit: e.target.value })}
          className="w-full border border-cream-dark rounded px-2 py-1.5 bg-white text-sm" />
      </div>
      <div>
        <label className="block text-xs text-ink-soft mb-1">Reorder at</label>
        <input type="number" step="any" value={draft.reorder_level ?? ''}
          onChange={(e) => setDraft({ ...draft, reorder_level: e.target.value ? parseFloat(e.target.value) : null })}
          className="w-full border border-cream-dark rounded px-2 py-1.5 bg-white text-sm" />
      </div>
      <div>
        <label className="block text-xs text-ink-soft mb-1">Critical at</label>
        <input type="number" step="any" value={draft.critical_level ?? ''}
          onChange={(e) => setDraft({ ...draft, critical_level: e.target.value ? parseFloat(e.target.value) : null })}
          className="w-full border border-cream-dark rounded px-2 py-1.5 bg-white text-sm" />
      </div>
      <div className="col-span-2 sm:col-span-5 flex gap-3 text-sm mt-1">
        <button onClick={() => onSave(draft)} className="text-accent font-medium">Save</button>
        <button onClick={onCancel} className="text-ink-soft">Cancel</button>
      </div>
    </div>
  )
}