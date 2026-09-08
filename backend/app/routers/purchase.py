"""
The purchase list workflow: view what needs buying, and move entries
through needs_purchase -> ordered -> partially_received -> received.
The /check endpoint runs the deterministic scan from purchase_logic.py -
anyone can trigger it manually for now; Phase 11 wires it to a schedule.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_pool
from app.security import get_current_user, CurrentUser
from app.dependencies import require_role
from app.schemas import PurchaseListEntryOut, PurchaseListEntryUpdate
from app.purchase_logic import run_low_stock_check
from app.inventory_logic import calculate_status
from app.audit import record_audit

router = APIRouter(prefix="/api/v1/purchase-list", tags=["purchase list"])

_VALID_STATUSES = ("needs_purchase", "ordered", "partially_received", "received")

_SELECT = """
    select p.id, p.item_id, p.status, p.quantity_ordered, p.created_at, p.updated_at,
           i.name as item_name, i.unit, i.current_stock,
           i.monthly_requirement, i.monthly_requirement_min, i.monthly_requirement_max,
           l.name as location_name
    from public.purchase_list_entries p
    join public.inventory_items i on i.id = p.item_id
    join public.locations l on l.id = i.location_id
"""


@router.get("", response_model=list[PurchaseListEntryOut])
async def list_purchase_entries(
    status: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user),
):
    pool = get_pool()
    if status:
        if status not in _VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(_VALID_STATUSES)}")
        rows = await pool.fetch(f"{_SELECT} where p.status = $1 order by p.created_at desc", status)
    else:
        rows = await pool.fetch(f"{_SELECT} order by p.created_at desc")
    return [dict(r) for r in rows]


@router.patch("/{entry_id}", response_model=PurchaseListEntryOut)
async def update_purchase_entry(
    entry_id: UUID,
    body: PurchaseListEntryUpdate,
    user: CurrentUser = Depends(require_role("manager", "admin")),
):
    if body.status and body.status not in _VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(_VALID_STATUSES)}")

    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        before = await conn.fetchrow(f"{_SELECT} where p.id = $1", entry_id)
        if before is None:
            raise HTTPException(status_code=404, detail="Purchase list entry not found.")

        updates = body.model_dump(exclude_unset=True)
        if updates:
            updates["updated_by"] = user.id
            set_clauses = ", ".join(f"{key} = ${i+2}" for i, key in enumerate(updates.keys()))
            await conn.execute(
                f"update public.purchase_list_entries set {set_clauses} where id = $1",
                entry_id, *updates.values(),
            )

        after = await conn.fetchrow(f"{_SELECT} where p.id = $1", entry_id)
        await record_audit(conn, user.id, "purchase_entry_updated", "purchase_list_entry",
                            str(entry_id), dict(before), dict(after))
    return dict(after)


@router.post("/check")
async def trigger_low_stock_check(user: CurrentUser = Depends(get_current_user)):
    """
    Manually runs the same deterministic scan Phase 11's scheduler will
    call automatically. Open to any logged-in role for now since it only
    ever reads stock and creates purchase-list entries - it can't change
    stock or delete anything, so there's nothing destructive to restrict.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await run_low_stock_check(conn)
    return result