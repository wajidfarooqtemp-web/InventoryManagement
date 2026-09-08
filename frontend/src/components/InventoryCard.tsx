import { useState } from 'react'
import { StatusBadge } from './StatusBadge'
import { ItemPhoto } from './ItemPhoto'
import { QuickActionSheet } from './QuickActionSheet'

type Item = {
  id: string
  name: string
  location_name: string
  unit: string
  current_stock: number
  monthly_requirement: number | null
  monthly_requirement_min: number | null
  monthly_requirement_max: number | null
  requirement_is_estimate: boolean
  needs_confirmation: boolean
  image_path: string | null
  status: 'GOOD' | 'LOW' | 'CRITICAL' | 'OUT_OF_STOCK'
}

// Same range-safety rule as the Overview page: a genuine 3-5/month range
// is shown as a range, never quietly averaged into one fake number.
function formatRequirement(item: Item): string {
  if (item.monthly_requirement != null) {
    return `${item.monthly_requirement} ${item.unit}/month${item.requirement_is_estimate ? ' (est.)' : ''}`
  }
  if (item.monthly_requirement_min != null && item.monthly_requirement_max != null) {
    return `${item.monthly_requirement_min}–${item.monthly_requirement_max} ${item.unit}/month`
  }
  return 'Requirement not set'
}

export function InventoryCard({ item, onStockChanged }: { item: Item; onStockChanged: () => void }) {
  const [activeAction, setActiveAction] = useState<'receive' | 'use' | null>(null)

  return (
    <>
      <div className="bg-white/60 border border-cream-dark rounded-lg overflow-hidden flex flex-col">
        <ItemPhoto name={item.name} imagePath={item.image_path} />

        <div className="p-4 flex-1 flex flex-col">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="font-medium">{item.name}</p>
              <p className="text-xs text-ink-soft">{item.location_name}</p>
            </div>
            <StatusBadge status={item.status} />
          </div>

          <p className="mt-3 text-2xl font-heading">{item.current_stock} <span className="text-base font-body text-ink-soft">{item.unit}</span></p>
          <p className="text-sm text-ink-soft">{formatRequirement(item)}</p>

          {item.needs_confirmation && (
            <p className="text-xs text-status-low mt-1">⚠ Data needs confirmation</p>
          )}

          {/* Section 14: the two most common actions live right on the card -
              no navigating into a detail screen just to record usage. */}
          <div className="mt-4 grid grid-cols-2 gap-2">
            <button
              onClick={() => setActiveAction('use')}
              className="border border-cream-dark rounded-lg py-2 text-sm font-medium hover:border-accent"
            >
              − Used
            </button>
            <button
              onClick={() => setActiveAction('receive')}
              className="border border-cream-dark rounded-lg py-2 text-sm font-medium hover:border-accent"
            >
              + Received
            </button>
          </div>
        </div>
      </div>

      {activeAction && (
        <QuickActionSheet
          itemId={item.id}
          itemName={item.name}
          unit={item.unit}
          action={activeAction}
          onClose={() => setActiveAction(null)}
          onSuccess={onStockChanged}
        />
      )}
    </>
  )
}