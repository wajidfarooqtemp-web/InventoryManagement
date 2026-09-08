"""
The deterministic low-stock check described in the architecture doc,
Section 22. No AI - just current_stock compared against each item's own
configurable thresholds (calculate_status, reused from Phase 3).

Design choice worth knowing: this only ever CREATES a fresh
'needs_purchase' entry when an item is low AND has no existing entry
still in progress. It never auto-closes an entry when stock recovers -
if stock went back up some other way (e.g. an adjustment) without a
purchase actually happening, a person should look at that and decide
what the entry should say, not have it silently vanish.
"""
import asyncpg
from app.inventory_logic import calculate_status

# An item with an entry in any of these states already has an active
# purchase workflow in progress - don't create a second one on top of it.
_ACTIVE_STATUSES = ("needs_purchase", "ordered", "partially_received")


async def run_low_stock_check(conn: asyncpg.Connection) -> dict:
    items = await conn.fetch(
        "select id, current_stock, reorder_level, critical_level from public.inventory_items where active = true"
    )

    created = []
    for item in items:
        status = calculate_status(item["current_stock"], item["reorder_level"], item["critical_level"])
        if status not in ("LOW", "CRITICAL", "OUT_OF_STOCK"):
            continue

        has_active_entry = await conn.fetchval(
            f"""
            select 1 from public.purchase_list_entries
            where item_id = $1 and status = any($2::purchase_status[])
            """,
            item["id"], list(_ACTIVE_STATUSES),
        )
        if has_active_entry:
            continue

        row = await conn.fetchrow(
            """
            insert into public.purchase_list_entries (item_id, status)
            values ($1, 'needs_purchase')
            returning id, item_id
            """,
            item["id"],
        )
        created.append({"id": str(row["id"]), "item_id": str(row["item_id"]), "status_at_check": status})

    return {"items_checked": len(items), "entries_created": created}