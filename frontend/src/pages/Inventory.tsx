import { useEffect, useState, useCallback } from 'react'
import { apiFetch } from '../lib/apiClient'
import { InventoryCard } from '../components/InventoryCard'

type Location = { id: string; name: string }
type Category = { id: string; name: string }
type Item = Parameters<typeof InventoryCard>[0]['item']

export function Inventory() {
  const [items, setItems] = useState<Item[]>([])
  const [locations, setLocations] = useState<Location[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [search, setSearch] = useState('')
  const [locationFilter, setLocationFilter] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters live in the URL's query string params sent to the backend,
  // not filtered client-side - so this stays correct even as the
  // catalog grows beyond what's convenient to fetch all at once.
  const loadItems = useCallback(() => {
    setLoading(true)
    const params = new URLSearchParams()
    if (search) params.set('q', search)
    if (locationFilter) params.set('location_id', locationFilter)
    if (categoryFilter) params.set('category_id', categoryFilter)
    if (statusFilter) params.set('status', statusFilter)

    apiFetch(`/api/v1/inventory?${params.toString()}`)
      .then(setItems)
      .catch(() => setError('Could not load inventory. Please try again.'))
      .finally(() => setLoading(false))
  }, [search, locationFilter, categoryFilter, statusFilter])

  useEffect(() => {
    apiFetch('/api/v1/locations').then(setLocations).catch(() => {})
    apiFetch('/api/v1/categories').then(setCategories).catch(() => {})
  }, [])

  // Debounced search: wait 300ms after typing stops before hitting the API.
  useEffect(() => {
    const timer = setTimeout(loadItems, 300)
    return () => clearTimeout(timer)
  }, [loadItems])

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row gap-3">
        <input
          type="text" placeholder="Search items…" value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 border border-cream-dark rounded px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-accent"
        />
        <select value={locationFilter} onChange={(e) => setLocationFilter(e.target.value)}
          className="border border-cream-dark rounded px-3 py-2 bg-white">
          <option value="">All locations</option>
          {locations.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
        </select>
        <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}
          className="border border-cream-dark rounded px-3 py-2 bg-white">
          <option value="">All categories</option>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-cream-dark rounded px-3 py-2 bg-white">
          <option value="">All statuses</option>
          <option value="GOOD">Good</option>
          <option value="LOW">Low</option>
          <option value="CRITICAL">Critical</option>
          <option value="OUT_OF_STOCK">Out of stock</option>
        </select>
      </div>

      {loading && <p className="text-ink-soft">Loading…</p>}
      {error && <p className="text-status-critical">{error}</p>}
      {!loading && !error && items.length === 0 && (
        <p className="text-ink-soft">No items match these filters.</p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {items.map((item) => (
          <InventoryCard key={item.id} item={item} onStockChanged={loadItems} />
        ))}
      </div>
    </div>
  )
}