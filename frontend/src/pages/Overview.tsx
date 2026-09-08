import { useEffect, useState } from 'react'
import { apiFetch } from '../lib/apiClient'
import { StatusBadge } from '../components/StatusBadge'

type NeedsAttentionItem = {
  item_id: string
  item_name: string
  location_name: string
  unit: string
  current_stock: number
  monthly_requirement: number | null
  monthly_requirement_min: number | null
  monthly_requirement_max: number | null
  status: 'LOW' | 'CRITICAL' | 'OUT_OF_STOCK'
}

type RecentActivity = {
  id: string
  item_name: string
  location_name: string
  movement_type: string
  quantity: number
  created_by_name: string | null
  created_at: string
}

type OverviewData = {
  total_active_items: number
  total_locations: number
  items_good: number
  items_low: number
  items_critical: number
  items_out_of_stock: number
  items_needs_confirmation: number
  needs_attention: NeedsAttentionItem[]
  recent_activity: RecentActivity[]
}

// Turns a requirement (fixed number OR a genuine range) into one readable
// string, without ever collapsing a range into a fake average (e.g.
// Milkmaid's 3-5/month must never silently become "4").
function formatRequirement(item: NeedsAttentionItem): string {
  if (item.monthly_requirement != null) return `${item.monthly_requirement} ${item.unit}/month`
  if (item.monthly_requirement_min != null && item.monthly_requirement_max != null) {
    return `${item.monthly_requirement_min}–${item.monthly_requirement_max} ${item.unit}/month`
  }
  return 'Requirement not set'
}

function formatMovement(m: RecentActivity): string {
  const sign = ['RECEIVE', 'TRANSFER_IN'].includes(m.movement_type) ? '+' : '−'
  const verb: Record<string, string> = {
    RECEIVE: 'received', USE: 'used', ADJUSTMENT: 'adjusted',
    TRANSFER_IN: 'transferred in', TRANSFER_OUT: 'transferred out',
  }
  return `${sign}${m.quantity} ${verb[m.movement_type] ?? m.movement_type.toLowerCase()}`
}

export function Overview() {
  const [data, setData] = useState<OverviewData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    apiFetch('/api/v1/overview')
      .then(setData)
      .catch(() => setError('Could not load the inventory overview. Please try again.'))
  }, [])

  if (error) return <p className="text-status-critical">{error}</p>
  if (!data) return <p className="text-ink-soft">Loading overview…</p>

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* The "5-10 second understanding" top row, per Section 52 */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <SummaryCard label="Active items" value={data.total_active_items} />
        <SummaryCard label="Locations" value={data.total_locations} />
        <SummaryCard label="Good" value={data.items_good} tone="good" />
        <SummaryCard
          label="Needs attention"
          value={data.items_low + data.items_critical + data.items_out_of_stock}
          tone="warn"
        />
        <SummaryCard label="Needs confirmation" value={data.items_needs_confirmation} tone="muted" />
      </div>

      <section>
        <h2 className="font-heading text-lg mb-3">Needs Attention</h2>
        {data.needs_attention.length === 0 ? (
          <p className="text-ink-soft text-sm">Nothing needs attention right now.</p>
        ) : (
          <div className="bg-white/60 border border-cream-dark rounded-lg divide-y divide-cream-dark">
            {data.needs_attention.map((item) => (
              <div key={item.item_id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="font-medium">{item.item_name}</p>
                  <p className="text-sm text-ink-soft">
                    {item.location_name} · {item.current_stock} {item.unit} remaining · {formatRequirement(item)}
                  </p>
                </div>
                <StatusBadge status={item.status} />
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="font-heading text-lg mb-3">Recent Activity</h2>
        {data.recent_activity.length === 0 ? (
          <p className="text-ink-soft text-sm">No activity recorded yet.</p>
        ) : (
          <div className="bg-white/60 border border-cream-dark rounded-lg divide-y divide-cream-dark">
            {data.recent_activity.map((m) => (
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
          </div>
        )}
      </section>
    </div>
  )
}

function SummaryCard({
  label, value, tone = 'default',
}: { label: string; value: number; tone?: 'default' | 'good' | 'warn' | 'muted' }) {
  const toneClasses = { default: 'text-ink', good: 'text-status-good', warn: 'text-status-low', muted: 'text-ink-soft' }[tone]
  return (
    <div className="bg-white/60 border border-cream-dark rounded-lg p-4">
      <p className={`text-2xl font-heading ${toneClasses}`}>{value}</p>
      <p className="text-sm text-ink-soft">{label}</p>
    </div>
  )
}