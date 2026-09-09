import { useEffect, useState } from 'react'
import { apiFetch } from '../lib/apiClient'
import { useAuth } from '../contexts/AuthContext'

type Entry = {
  id: string
  item_name: string
  location_name: string
  unit: string
  current_stock: number
  monthly_requirement: number | null
  status: string
  quantity_ordered: number | null
}

const STATUS_FLOW = ['needs_purchase', 'ordered', 'partially_received', 'received']

export function PurchaseList() {
  const { profile } = useAuth()
  const canEdit = profile?.role === 'manager' || profile?.role === 'admin'
  const [entries, setEntries] = useState<Entry[]>([])
  const [checking, setChecking] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  function load() {
    apiFetch('/api/v1/purchase-list').then(setEntries)
  }
  useEffect(load, [])

  async function runCheck() {
    setChecking(true)
    try {
      const result = await apiFetch('/api/v1/purchase-list/check', { method: 'POST' })
      setMessage(`Checked ${result.items_checked} items - ${result.entries_created.length} new entries added.`)
      load()
    } catch {
      setMessage('Could not run the check. Please try again.')
    } finally {
      setChecking(false)
    }
  }

  async function updateStatus(entry: Entry, status: string) {
    await apiFetch(`/api/v1/purchase-list/${entry.id}`, { method: 'PATCH', body: JSON.stringify({ status }) })
    load()
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-lg">Purchase List</h2>
        <button onClick={runCheck} disabled={checking}
          className="bg-accent text-white rounded px-4 py-1.5 text-sm disabled:opacity-50">
          {checking ? 'Checking…' : 'Run low-stock check'}
        </button>
      </div>
      {message && <p className="text-sm text-ink-soft">{message}</p>}

      <div className="bg-white/60 border border-cream-dark rounded-lg divide-y divide-cream-dark">
        {entries.map((entry) => (
          <div key={entry.id} className="flex items-center justify-between px-4 py-3 text-sm">
            <div>
              <p className="font-medium">{entry.item_name}</p>
              <p className="text-ink-soft">
                {entry.location_name} · {entry.current_stock} {entry.unit} remaining
                {entry.monthly_requirement != null && ` · needs ${entry.monthly_requirement} ${entry.unit}/month`}
              </p>
            </div>
            {canEdit ? (
              <select value={entry.status} onChange={(e) => updateStatus(entry, e.target.value)}
                className="border border-cream-dark rounded px-2 py-1 bg-white text-sm">
                {STATUS_FLOW.map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
              </select>
            ) : (
              <span className="text-ink-soft">{entry.status.replace('_', ' ')}</span>
            )}
          </div>
        ))}
        {entries.length === 0 && <p className="p-4 text-ink-soft text-sm">Nothing on the purchase list right now.</p>}
      </div>
    </div>
  )
}