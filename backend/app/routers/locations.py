"""
Locations: everyone logged in can read; only manager/admin can write.
This mirrors the RLS policies from Phase 1 - RLS is the backup, this is
the enforcement that actually runs on every request.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_pool
from app.security import get_current_user, CurrentUser
from app.dependencies import require_role
from app.schemas import LocationOut, LocationCreate, LocationUpdate
from app.audit import record_audit

router = APIRouter(prefix="/api/v1/locations", tags=["locations"])


@router.get("", response_model=list[LocationOut])
async def list_locations(active: Optional[bool] = True, user: CurrentUser = Depends(get_current_user)):
    """
    Same pattern as categories.py: defaults to active-only for normal use,
    but the admin screen calls this twice (active=true and active=false)
    to show both groups - this filter is what makes that actually work
    instead of returning the same full list both times.
    """
    pool = get_pool()
    rows = await pool.fetch("select id, name, active from public.locations where active = $1 order by name", active)
    return [dict(r) for r in rows]


@router.post("", response_model=LocationOut, status_code=201)
async def create_location(body: LocationCreate, user: CurrentUser = Depends(require_role("manager", "admin"))):
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        if await conn.fetchval("select id from public.locations where name = $1", body.name):
            raise HTTPException(status_code=409, detail="A location with this name already exists.")
        row = await conn.fetchrow(
            "insert into public.locations (name) values ($1) returning id, name, active",
            body.name,
        )
        await record_audit(conn, user.id, "location_created", "location", str(row["id"]), None, dict(row))
    return dict(row)

@router.delete("/{location_id}", status_code=204)
async def delete_location(location_id: UUID, user: CurrentUser = Depends(require_role("admin"))):
    """
    Same safety rule as category deletion: only allowed when no item
    references this location at all. Deactivating remains the right
    move otherwise.
    """
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        before = await conn.fetchrow("select id, name, active from public.locations where id=$1", location_id)
        if before is None:
            raise HTTPException(status_code=404, detail="Location not found.")

        item_count = await conn.fetchval(
            "select count(*) from public.inventory_items where location_id=$1", location_id
        )
        if item_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete - {item_count} item(s) still use this location. Reassign or deactivate them first.",
            )

        await conn.execute("delete from public.locations where id=$1", location_id)
        await record_audit(conn, user.id, "location_deleted", "location", str(location_id), dict(before), None)

@router.patch("/{location_id}", response_model=LocationOut)
async def update_location(location_id: str, body: LocationUpdate, user: CurrentUser = Depends(require_role("manager", "admin"))):
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        before = await conn.fetchrow("select id, name, active from public.locations where id = $1", location_id)
        if before is None:
            raise HTTPException(status_code=404, detail="Location not found.")

        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(before)

        # Column names here come only from LocationUpdate's own fixed field
        # list, never from raw client input - so building SET this way is
        # safe. Values stay fully parameterized below.
        set_clauses = ", ".join(f"{key} = ${i+2}" for i, key in enumerate(updates.keys()))
        row = await conn.fetchrow(
            f"update public.locations set {set_clauses} where id = $1 returning id, name, active",
            location_id, *updates.values(),
        )
        await record_audit(conn, user.id, "location_updated", "location", location_id, dict(before), dict(row))
    return dict(row)