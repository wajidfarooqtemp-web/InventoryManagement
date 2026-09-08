"""
Deterministic business rules that don't belong to any one router.
Kept separate so the low-stock automation job and dashboard (later phases)
can reuse the exact same logic instead of re-implementing it.
"""


def calculate_status(current_stock: float, reorder_level: float | None, critical_level: float | None) -> str:
    """Thresholds are per-item and optional (architecture doc, Section 49)."""
    if current_stock <= 0:
        return "OUT_OF_STOCK"
    if critical_level is not None and current_stock <= critical_level:
        return "CRITICAL"
    if reorder_level is not None and current_stock <= reorder_level:
        return "LOW"
    return "GOOD"