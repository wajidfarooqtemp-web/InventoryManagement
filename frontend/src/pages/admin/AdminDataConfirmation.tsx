import { useEffect, useState } from 'react'
import { apiFetch } from '../../lib/apiClient'

type FlaggedItem = {
  id: string
  name: string
  location_name: string
  category_name: string
  unit: string
  monthly_requirement: number | null
  monthly_requirement_min: number | null
  monthly_requirement_max: number | null
  confirmation_note: string | null
}

// The Section 51 "queue" - every item still flagged needs_confirmation,
// resolved one at a time by editing its name/requirement here directly.
export function AdminDataConfirmation() {
  const [items, setItems] = useState<FlaggedItem[]>([])
  const [drafts, setDrafts] = useState<Record<string, { name: string; monthly_requirement: string }>>({})
  const [message, setMessage] = useState<string | null>(null)

  function load() {
    apiFetch('/api/v1/data-confirmation').then((rows: FlaggedItem[]) => {
      setItems(rows)
      const initial: typeof drafts = {}
      rows.forEach((r) => {
        initial[r.id] = { name: r.name, monthly_requirement: r.monthly_requirement?.toString() ?? '' }
      })
      setDrafts(initial)
    })
  }
  useEffect(load, [])

  async function resolve(item: FlaggedItem) {
    const draft = drafts[item.id]
    try {
      await apiFetch(`/api/v1/data-confirmation/${item.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          name: draft.name,
          monthly_requirement: draft.monthly_requirement ? parseFloat(draft.monthly_requirement) : null,
        }),
      })
      setMessage(`${draft.name} confirmed and removed from this list.`)
      load()
    } catch {
      setMessage('Could not save. Please try again.')
    }
  }

  if (items.length === 0) {
    return <p className="text-ink-soft">Nothing needs confirmation right now.</p>
  }

  return (
    <div>
      {message && <p className="text-sm text-status-good mb-3">{message}</p>}
      <div className="bg-white/60 border border-cream-dark rounded-lg divide-y divide-cream-dark">
        {items.map((item) => (
          <div key={item.id} className="p-4">
            <p className="text-sm text-status-low mb-2">⚠ {item.confirmation_note}</p>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                value={drafts[item.id]?.name ?? ''}
                onChange={(e) => setDrafts({ ...drafts, [item.id]: { ...drafts[item.id], name: e.target.value } })}
                placeholder="Confirmed item name"
                className="flex-1 border border-cream-dark rounded px-3 py-1.5 bg-white text-sm"
              />
              <input
                type="number" step="any"
                value={drafts[item.id]?.monthly_requirement ?? ''}
                onChange={(e) => setDrafts({ ...drafts, [item.id]: { ...drafts[item.id], monthly_requirement: e.target.value } })}
                placeholder={`Monthly requirement (${item.unit})`}
                className="w-48 border border-cream-dark rounded px-3 py-1.5 bg-white text-sm"
              />
              <button onClick={() => resolve(item)} className="bg-accent text-white rounded px-4 text-sm">
                Confirm
              </button>
            </div>
            <p className="text-xs text-ink-soft mt-2">{item.location_name} · {item.category_name}</p>
          </div>
        ))}
      </div>
    </div>
  )
}