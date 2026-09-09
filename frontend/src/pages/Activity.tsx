import { useEffect, useState, useCallback } from 'react'
import { apiFetch } from '../lib/apiClient'

type Movement = {
  id: string
  item_name: string
  location_name: string
  movement_type: string
  quantity: number
  resulting_stock: number
  reason: string | null
  created_by_name: string | null
  created_at: string
}
type Location = { id: string; name: string }

const MOVEMENT_TYPES = ['RECEIVE', 'USE', 'ADJUSTMENT', 'TRANSFER_IN', 'TRANSFER_OUT']

export function Activity() {
  const [movements, setMovements] = useState<Movement[]>([])
  const [locations, setLocations] = useState<Location[]>([])
  const [locationFilter, setLocationFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const LIMIT = 30

  const load = useCallback((reset: boolean) => {
    const params = new URLSearchParams()
    if (locationFilter) params.set('location_id', locationFilter)
    if (typeFilter) params.set('movement_type', typeFilter)
    params.set('limit', String(LIMIT))
    params.set('offset', String(reset ? 0 : offset))

    apiFetch(`/api/v1/activity?${params.toString()}`).then((rows: Movement[]) => {
      setMovements(reset ? rows : (prev) => [...prev, ...rows])
      setHasMore(rows.length === LIMIT)
      setOffset(reset ? LIMIT : offset + LIMIT)
    })
  }, [locationFilter, typeFilter, offset])

  useEffect(() => {
    apiFetch('/api/v1/locations').then(setLocations)
  }, [])

  // Filters changing resets the feed from the top, rather than appending.
  useEffect(() => {
    setOffset(0)
    load(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locationFilter, typeFilter])

  function formatMovement(m: Movement): string {
    const sign = ['RECEIVE', 'TRANSFER_IN'].includes(m.movement_type) ? '+' : '−'
    return `${sign}${m.quantity}${m.reason ? ` · ${m.reason}` : ''}`
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <div className="flex gap-3">
        <select value={locationFilter} onChange={(e) => setLocationFilter(e.target.value)}
          className="border border-cream-dark rounded px-3 py-2 bg-white text-sm">
          <option value="">All locations</option>
          {locations.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
        </select>
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}
          className="border border-cream-dark rounded px-3 py-2 bg-white text-sm">
          <option value="">All actions</option>
          {MOVEMENT_TYPES.map((t) => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
        </select>
      </div>

      <div className="bg-white/60 border border-cream-dark rounded-lg divide-y divide-cream-dark">
        {movements.map((m) => (
          <div key={m.id} className="flex items-center justify-between px-4 py-3 text-sm">
            <div>
              <span className="font-medium">{m.item_name}</span>
              <span className="text-ink-soft"> · {m.location_name} · {formatMovement(m)}</span>
            </div>
            <span className="text-ink-soft">
              {m.created_by_name ?? 'System'} · {new Date(m.created_at).toLocaleString()}
            </span>
          </div>
        ))}
        {movements.length === 0 && <p className="p-4 text-ink-soft text-sm">No activity matches these filters.</p>}
      </div>

      {hasMore && (
        <button onClick={() => load(false)} className="text-accent text-sm">Load more</button>
      )}
    </div>
  )
}