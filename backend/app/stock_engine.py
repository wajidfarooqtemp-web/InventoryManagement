"""
The core atomic stock engine. This is the ONLY place that writes to
stock_movements or changes inventory_items.current_stock, anywhere in the
backend. Must be called from inside an already-open transaction, because a
Transfer needs to call this twice (once per item) and have both succeed
or neither happen.
"""
import asyncpg
from fastapi import HTTPException
from app.periods import get_or_create_current_period


async def create_movement(
    conn: asyncpg.Connection,
    item_id,
    movement_type: str,
    quantity: float,
    created_by: str | None,
    idempotency_key: str,
    reason: str | None = None,
    related_transfer_id=None,
) -> tuple[dict, bool]:
    # --- Idempotency check FIRST (Section 9) ---
    # If this exact action was already recorded, hand back the original
    # result instead of erroring or applying it a second time. This is
    # what makes a double-tapped button or a retried network request safe.
    existing = await conn.fetchrow(
        "select * from public.stock_movements where item_id=$1 and idempotency_key=$2",
        item_id, idempotency_key,
    )
    if existing:
        return dict(existing), False

    # --- Row lock for concurrency safety (Section 8) ---
    # "FOR UPDATE" makes a second simultaneous request for the SAME item
    # wait here until this transaction finishes - so two people tapping
    # "Used" on Rice at the exact same moment can never both read the same
    # starting number and silently overwrite each other's result.
    item = await conn.fetchrow(
        "select id, current_stock from public.inventory_items where id=$1 for update", item_id
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found.")

    current = float(item["current_stock"])
    if movement_type in ("RECEIVE", "OPENING_BALANCE", "TRANSFER_IN"):
        new_stock = current + quantity
    elif movement_type in ("USE", "TRANSFER_OUT"):
        new_stock = current - quantity
    elif movement_type == "ADJUSTMENT":
        new_stock = current + quantity  # quantity arrives already signed
    else:
        raise ValueError(f"Unknown movement type: {movement_type}")

    if new_stock < 0:
        raise HTTPException(status_code=400, detail="This action would take stock below zero.")

    period_id = await get_or_create_current_period(conn)

    try:
        row = await conn.fetchrow(
            """
            insert into public.stock_movements
                (item_id, period_id, movement_type, quantity, resulting_stock,
                 reason, related_transfer_id, idempotency_key, created_by)
            values ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            returning *
            """,
            item_id, period_id, movement_type, quantity, new_stock,
            reason, related_transfer_id, idempotency_key, created_by,
        )
    except asyncpg.UniqueViolationError:
        # Lost a race against a truly simultaneous duplicate request that
        # inserted a split second earlier - return that one's result.
        existing = await conn.fetchrow(
            "select * from public.stock_movements where item_id=$1 and idempotency_key=$2",
            item_id, idempotency_key,
        )
        return dict(existing), False

    await conn.execute(
        "update public.inventory_items set current_stock=$2 where id=$1", item_id, new_stock
    )
    return dict(row), True