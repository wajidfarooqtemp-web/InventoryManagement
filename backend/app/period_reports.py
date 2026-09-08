"""
Turns raw stock_movements rows into the opening/received/used/adjustments/
closing summary described in the architecture doc's Section 6. This is
just arithmetic over what Phase 4 already wrote - no new data is created
here, only read and combined.
"""
import asyncpg

# Every movement type that can appear in a period, mapped to how it affects
# the running total. OPENING_BALANCE isn't listed as +/- here because it
# IS the starting point, not something added to it.
_ADDS = {"RECEIVE", "TRANSFER_IN"}
_SUBTRACTS = {"USE", "TRANSFER_OUT"}
# ADJUSTMENT is signed already (Phase 4), so it's added either way.


async def get_period_summary(conn: asyncpg.Connection, period_id, item_id) -> dict:
    rows = await conn.fetch(
        """
        select movement_type, sum(quantity) as total
        from public.stock_movements
        where period_id = $1 and item_id = $2
        group by movement_type
        """,
        period_id, item_id,
    )
    totals = {r["movement_type"]: float(r["total"]) for r in rows}

    opening = totals.get("OPENING_BALANCE", 0.0)
    received = totals.get("RECEIVE", 0.0)
    used = totals.get("USE", 0.0)
    adjustments = totals.get("ADJUSTMENT", 0.0)
    transfers_in = totals.get("TRANSFER_IN", 0.0)
    transfers_out = totals.get("TRANSFER_OUT", 0.0)

    closing = opening + received - used + adjustments + transfers_in - transfers_out

    return {
        "opening_stock": opening,
        "received": received,
        "used": used,
        "adjustments": adjustments,
        "transfers_in": transfers_in,
        "transfers_out": transfers_out,
        "closing_stock": closing,
    }