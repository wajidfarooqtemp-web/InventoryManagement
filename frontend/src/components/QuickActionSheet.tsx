import { useState } from 'react'
import { apiFetch } from '../lib/apiClient'
import { getQuantityShortcuts, newIdempotencyKey } from '../lib/units'

type Props = {
  itemId: string
  itemName: string
  unit: string
  action: 'receive' | 'use'
  onClose: () => void
  onSuccess: (newStock: number, newStatus: string) => void
}

// The entire "tap item -> tap Used/Received -> tap quantity -> done" flow
// from Section 15 lives in this one component, reused for both actions
// and for every unit type via getQuantityShortcuts.
export function QuickActionSheet({ itemId, itemName, unit, action, onClose, onSuccess }: Props) {
  const [customValue, setCustomValue] = useState('')
  const [showCustom, setShowCustom] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<{ quantity: number; newStock: number } | null>(null)

  // Generated once when the sheet opens, not per-request - so if this
  // exact submission is retried, it's the SAME key both times.
  const [idempotencyKey] = useState(newIdempotencyKey)

  async function submit(quantity: number) {
    if (submitting || quantity <= 0) return
    setSubmitting(true)
    setError(null)
    try {
      const result = await apiFetch(`/api/v1/inventory/${itemId}/${action}`, {
        method: 'POST',
        body: JSON.stringify({ quantity, idempotency_key: idempotencyKey }),
      })
      setSuccess({ quantity, newStock: result.current_stock })
      onSuccess(result.current_stock, result.status)
    } catch {
      setError('Could not save this. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const shortcuts = getQuantityShortcuts(unit)
  const verb = action === 'receive' ? 'Received' : 'Used'

  return (
    <div className="fixed inset-0 bg-ink/40 flex items-end sm:items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-cream w-full sm:max-w-sm rounded-t-2xl sm:rounded-2xl p-6"
        onClick={(e) => e.stopPropagation()}
      >
        {success ? (
          // Success state (Section 42) - confirms what happened and the
          // new number, so there's no doubt the tap registered.
          <div className="text-center py-4">
            <p className="text-status-good text-2xl mb-2">✓</p>
            <p className="font-medium">{itemName} updated</p>
            <p className="text-ink-soft text-sm mt-1">
              {success.quantity} {unit} {verb.toLowerCase()}
            </p>
            <p className="text-ink-soft text-sm">Current stock: {success.newStock} {unit}</p>
            <button onClick={onClose} className="mt-4 text-accent font-medium">Done</button>
          </div>
        ) : (
          <>
            <p className="font-heading text-lg mb-1">{itemName}</p>
            <p className="text-ink-soft text-sm mb-4">How much was {verb.toLowerCase()}?</p>

            <div className="grid grid-cols-4 gap-2">
              {shortcuts.map((qty) => (
                <button
                  key={qty}
                  disabled={submitting}
                  onClick={() => submit(qty)}
                  className="border border-cream-dark rounded-lg py-3 font-medium hover:border-accent disabled:opacity-50"
                >
                  {qty} {unit}
                </button>
              ))}
              <button
                disabled={submitting}
                onClick={() => setShowCustom(true)}
                className="border border-cream-dark rounded-lg py-3 font-medium hover:border-accent disabled:opacity-50"
              >
                Other
              </button>
            </div>

            {showCustom && (
              <div className="mt-4 flex gap-2">
                <input
                  type="number" min="0" step="any" autoFocus
                  value={customValue}
                  onChange={(e) => setCustomValue(e.target.value)}
                  placeholder={`Amount in ${unit}`}
                  className="flex-1 border border-cream-dark rounded px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-accent"
                />
                <button
                  disabled={submitting || !customValue}
                  onClick={() => submit(parseFloat(customValue))}
                  className="bg-accent text-white rounded px-4 font-medium disabled:opacity-50"
                >
                  Confirm
                </button>
              </div>
            )}

            {error && <p className="text-status-critical text-sm mt-3">{error}</p>}

            <button onClick={onClose} className="w-full text-ink-soft text-sm mt-5">Cancel</button>
          </>
        )}
      </div>
    </div>
  )
}