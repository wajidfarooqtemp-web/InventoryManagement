"""
Handles the monthly "inventory period" concept. A period (e.g. "September
2026") is created lazily - the very first time anyone touches stock after
the month rolls over - never in advance, never overwritten.
"""
from datetime import date
import asyncpg


async def get_or_create_current_period(conn: asyncpg.Connection):
    today = date.today()
    year, month = today.year, today.month

    period = await conn.fetchrow(
        "select id from public.inventory_periods where year=$1 and month=$2", year, month
    )
    if period:
        return period["id"]

    period = await conn.fetchrow(
        "insert into public.inventory_periods (year, month) values ($1,$2) returning id",
        year, month,
    )
    period_id = period["id"]

    # On creation, snapshot every active item's CURRENT stock as this new
    # period's OPENING_BALANCE. This is what makes "what happened to Rice
    # in October" answerable later (Phase 5) - it always has a real
    # starting point, carried forward from wherever September left off.
    items = await conn.fetch("select id, current_stock from public.inventory_items where active=true")
    for item in items:
        await conn.execute(
            """
            insert into public.stock_movements
                (item_id, period_id, movement_type, quantity, resulting_stock, idempotency_key, created_by)
            values ($1, $2, 'OPENING_BALANCE', $3, $3, $4, null)
            """,
            item["id"], period_id, item["current_stock"], f"opening-balance-{period_id}",
        )
    return period_id