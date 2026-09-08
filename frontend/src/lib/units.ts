// Maps each unit to sensible tap-shortcut quantities (Section 15) - no
// typing needed for the common case. "Other" always available as an
// escape hatch for anything outside these.
const SHORTCUTS_BY_UNIT: Record<string, number[]> = {
  kg: [1, 5, 10, 25],
  litre: [1, 5, 10],
  box: [1, 2, 5],
  bag: [1, 2, 5],
  bottle: [1, 2],
  dozen: [1, 2, 4],
  cylinder: [1, 2],
  piece: [1, 5, 10, 20],
  packet: [1, 2, 5],
  can: [1, 2],
}

export function getQuantityShortcuts(unit: string): number[] {
  return SHORTCUTS_BY_UNIT[unit] ?? [1, 5, 10]
}

// One idempotency key per button tap, generated client-side. If the tap
// is retried (flaky network, accidental double-tap), the backend sees
// the same key twice and returns the original result instead of applying
// it again (Phase 4's create_movement).
export function newIdempotencyKey(): string {
  return crypto.randomUUID()
}