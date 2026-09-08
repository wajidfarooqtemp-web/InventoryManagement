"""
The "Data Requiring Confirmation" screen from Section 51 - surfaces every
item still flagged needs_confirmation=true, and lets manager/admin resolve
it. Resolving reuses the same PATCH /inventory/{id} logic conceptually,
but as its own endpoint so the frontend has one clear "queue" to work
through and clear it out.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_pool
from app.security import get_current_user, CurrentUser
from app.dependencies import require_role
from app.schemas import DataConfirmationOut, InventoryItemUpdate
from app.audit import record_audit

router = APIRouter(prefix="/api/v1/data-confirmation", tags=["data confirmation"])

_SELECT = """
    select i.id, i.name, l.name as location_name, c.name as category_name, i.unit,
           i.monthly_requirement, i.monthly_requirement_min, i.monthly_requirement_max,
           i.confirmation_note
    from public.inventory_items i
    join public.locations l on l.id = i.location_id
    join public.categories c on c.id = i.category_id
    where i.needs_confirmation = true and i.active = true
"""


@router.get("", response_model=list[DataConfirmationOut])
async def list_needing_confirmation(user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    rows = await pool.fetch(f"{_SELECT} order by i.name")
    return [dict(r) for r in rows]


@router.patch("/{item_id}", response_model=DataConfirmationOut)
async def resolve_confirmation(item_id: UUID, body: InventoryItemUpdate, user: CurrentUser = Depends(require_role("manager", "admin"))):
    """
    Accepts the same fields as a normal item edit (rename, set the real
    monthly requirement, etc.) and additionally clears needs_confirmation
    unless the caller explicitly wants to keep it flagged.
    """
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        before = await conn.fetchrow(
            "select * from public.inventory_items where id=$1 and active=true", item_id
        )
        if before is None:
            raise HTTPException(status_code=404, detail="Item not found.")

        updates = body.model_dump(exclude_unset=True)
        if "needs_confirmation" not in updates:
            updates["needs_confirmation"] = False  # resolving implies "no longer needs confirmation"
        updates["updated_by"] = user.id

        set_clauses = ", ".join(f"{key} = ${i+2}" for i, key in enumerate(updates.keys()))
        await conn.execute(
            f"update public.inventory_items set {set_clauses} where id = $1",
            item_id, *updates.values(),
        )
        after = await conn.fetchrow(f"{_SELECT.replace('where', 'where i.id = $1 and')}", item_id)
        await record_audit(conn, user.id, "data_confirmation_resolved", "inventory_item",
                            str(item_id), dict(before), dict(updates))

    if after is None:
        # It resolved successfully but no longer matches the "still needs
        # confirmation" filter used by _SELECT - that's the success case.
        pool2 = get_pool()
        row = await pool2.fetchrow(
            """
            select i.id, i.name, l.name as location_name, c.name as category_name, i.unit,
                   i.monthly_requirement, i.monthly_requirement_min, i.monthly_requirement_max,
                   i.confirmation_note
            from public.inventory_items i
            join public.locations l on l.id = i.location_id
            join public.categories c on c.id = i.category_id
            where i.id = $1
            """,
            item_id,
        )
        return dict(row)
    return dict(after)