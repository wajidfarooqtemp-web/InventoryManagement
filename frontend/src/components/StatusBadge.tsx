type Status = 'GOOD' | 'LOW' | 'CRITICAL' | 'OUT_OF_STOCK'

// Color AND text/icon together, always - never color alone (architecture
// doc, Section 12: works for colorblind users, clearer for everyone else too).
const STATUS_CONFIG: Record<Status, { label: string; classes: string; icon: string }> = {
  GOOD: { label: 'Good', classes: 'bg-status-good/10 text-status-good', icon: '●' },
  LOW: { label: 'Low', classes: 'bg-status-low/10 text-status-low', icon: '▲' },
  CRITICAL: { label: 'Critical', classes: 'bg-status-critical/10 text-status-critical', icon: '■' },
  OUT_OF_STOCK: { label: 'Out of stock', classes: 'bg-status-critical/20 text-status-critical', icon: '✕' },
}

export function StatusBadge({ status }: { status: Status }) {
  const config = STATUS_CONFIG[status]
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${config.classes}`}>
      <span aria-hidden="true">{config.icon}</span>
      {config.label}
    </span>
  )
}