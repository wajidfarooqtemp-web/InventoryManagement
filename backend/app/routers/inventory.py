"""
Inventory items: the master catalog. Everyone logged in can read;
manager/admin can create and edit metadata; only admin can
deactivate/reactivate (Section 19 - reactivation is treated as sensitive
as deactivation, since either one changes what the whole org sees).

IMPORTANT: nothing here ever changes current_stock. That happens only in
Phase 4, through a stock movement, inside its own transaction.
"""
from typing import Optional
from uuid import UUID
import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from app.rate_limit import limiter
from app.image_processing import validate_and_process_image
from app.storage import upload_image, sign_url, delete_image
from app.database import get_pool
from app.security import get_current_user, CurrentUser
from app.dependencies import require_role
from app.schemas import InventoryItemOut, InventoryItemCreate, InventoryItemUpdate
from app.audit import record_audit
from app.inventory_logic import calculate_status

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])

# Shared by every query below so location_name/category_name/status are
# always attached the same way, regardless of which endpoint is asking.
_BASE_SELECT = """
    select i.*, l.name as location_name, c.name as category_name
    from public.inventory_items i
    join public.locations l on l.id = i.location_id
    join public.categories c on c.id = i.category_id
"""


def _with_status(row) -> dict:
    d = dict(row)
    d["status"] = calculate_status(d["current_stock"], d["reorder_level"], d["critical_level"])
    return d
async def _attach_image_urls(items: list[dict]) -> list[dict]:
    """
    Signs a URL for every item that has an image, concurrently rather than
    one at a time - keeps list responses fast as more items get photos.
    Items with no image_path just get image_url = None.
    """
    async def resolve(item):
        item["image_url"] = await sign_url(item["image_path"]) if item.get("image_path") else None
        return item
    return list(await asyncio.gather(*(resolve(i) for i in items)))


@router.get("", response_model=list[InventoryItemOut])
async def list_inventory(
    location_id: Optional[UUID] = None,
    category_id: Optional[UUID] = None,
    active: Optional[bool] = True,
    status: Optional[str] = None,
    q: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user),
):
    """
    `status` isn't a real column - it's calculated in Python after
    fetching (see calculate_status), so filtering on it happens after
    the fact rather than in SQL. With ~60 items total this is negligible;
    if the catalog grows into the thousands, this is the first thing to
    move into SQL.
    """
    pool = get_pool()
    where_clauses, params = [], []

    def add_filter(sql_fragment: str, value):
        params.append(value)
        where_clauses.append(sql_fragment.format(len(params)))

    if active is not None:
        add_filter("i.active = ${}", active)
    if location_id is not None:
        add_filter("i.location_id = ${}", location_id)
    if category_id is not None:
        add_filter("i.category_id = ${}", category_id)
    if q:
        add_filter("i.name ilike ${}", f"%{q}%")

    where_sql = f"where {' and '.join(where_clauses)}" if where_clauses else ""
    rows = await pool.fetch(f"{_BASE_SELECT} {where_sql} order by i.name", *params)

    items = [_with_status(r) for r in rows]
    if status:
        items = [i for i in items if i["status"] == status.upper()]
    return await _attach_image_urls(items)


@router.get("/{item_id}", response_model=InventoryItemOut)
async def get_inventory_item(item_id: UUID, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    row = await pool.fetchrow(f"{_BASE_SELECT} where i.id = $1", item_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Item not found.")
    result = await _attach_image_urls([_with_status(row)])
    return result[0]


@router.post("", response_model=InventoryItemOut, status_code=201)
async def create_inventory_item(body: InventoryItemCreate, user: CurrentUser = Depends(require_role("manager", "admin"))):
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        # Reject a location/category that doesn't exist or is inactive -
        # never let a typo'd/guessed UUID silently create a broken item.
        if not await conn.fetchval("select 1 from public.locations where id = $1 and active = true", body.location_id):
            raise HTTPException(status_code=400, detail="Location not found or inactive.")
        if not await conn.fetchval("select 1 from public.categories where id = $1 and active = true", body.category_id):
            raise HTTPException(status_code=400, detail="Category not found or inactive.")
        if await conn.fetchval(
            "select 1 from public.inventory_items where name = $1 and location_id = $2",
            body.name, body.location_id,
        ):
            raise HTTPException(status_code=409, detail="An item with this name already exists at this location.")

        row = await conn.fetchrow(
            """
            insert into public.inventory_items (
                name, location_id, category_id, unit, package_size, package_unit,
                package_count, monthly_requirement, monthly_requirement_min,
                monthly_requirement_max, requirement_is_estimate, minimum_stock,
                reorder_level, critical_level, needs_confirmation, confirmation_note,
                notes, created_by, updated_by
            ) values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$18)
            returning id
            """,
            body.name, body.location_id, body.category_id, body.unit, body.package_size,
            body.package_unit, body.package_count, body.monthly_requirement,
            body.monthly_requirement_min, body.monthly_requirement_max,
            body.requirement_is_estimate, body.minimum_stock, body.reorder_level,
            body.critical_level, body.needs_confirmation, body.confirmation_note,
            body.notes, user.id,
        )
        full_row = await conn.fetchrow(f"{_BASE_SELECT} where i.id = $1", row["id"])
        await record_audit(conn, user.id, "item_created", "inventory_item", str(row["id"]), None, dict(full_row))
    return _with_status(full_row)


@router.patch("/{item_id}", response_model=InventoryItemOut)
async def update_inventory_item(item_id: UUID, body: InventoryItemUpdate, user: CurrentUser = Depends(require_role("manager", "admin"))):
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        before = await conn.fetchrow(f"{_BASE_SELECT} where i.id = $1", item_id)
        if before is None:
            raise HTTPException(status_code=404, detail="Item not found.")

        updates = body.model_dump(exclude_unset=True)
        if updates:
            updates["updated_by"] = user.id
            # Same safety note as locations.py: keys come only from
            # InventoryItemUpdate's fixed field list, never raw input.
            set_clauses = ", ".join(f"{key} = ${i+2}" for i, key in enumerate(updates.keys()))
            await conn.execute(
                f"update public.inventory_items set {set_clauses} where id = $1",
                item_id, *updates.values(),
            )

        after = await conn.fetchrow(f"{_BASE_SELECT} where i.id = $1", item_id)
        await record_audit(conn, user.id, "item_updated", "inventory_item", str(item_id), dict(before), dict(after))
    return _with_status(after)


async def _set_active(item_id: UUID, active: bool, user: CurrentUser) -> dict:
    """Soft delete only - row and history are never removed (Section 46)."""
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        before = await conn.fetchrow(f"{_BASE_SELECT} where i.id = $1", item_id)
        if before is None:
            raise HTTPException(status_code=404, detail="Item not found.")
        await conn.execute(
            "update public.inventory_items set active = $2, updated_by = $3 where id = $1",
            item_id, active, user.id,
        )
        after = await conn.fetchrow(f"{_BASE_SELECT} where i.id = $1", item_id)
        action = "item_reactivated" if active else "item_deactivated"
        await record_audit(conn, user.id, action, "inventory_item", str(item_id), dict(before), dict(after))
    return _with_status(after)


@router.patch("/{item_id}/deactivate", response_model=InventoryItemOut)
async def deactivate_item(item_id: UUID, user: CurrentUser = Depends(require_role("admin"))):
    return await _set_active(item_id, False, user)


@router.patch("/{item_id}/reactivate", response_model=InventoryItemOut)
async def reactivate_item(item_id: UUID, user: CurrentUser = Depends(require_role("admin"))):
    return await _set_active(item_id, True, user)
@router.post("/{item_id}/image", response_model=InventoryItemOut)
@limiter.limit("10/minute")
async def upload_item_image(
    request: Request,
    item_id: UUID,
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_role("manager", "admin")),
):
    raw_bytes = await file.read()
    processed_bytes, extension, content_type = validate_and_process_image(raw_bytes)

    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        before = await conn.fetchrow(f"{_BASE_SELECT} where i.id = $1", item_id)
        if before is None:
            raise HTTPException(status_code=404, detail="Item not found.")

        old_path = before["image_path"]
        new_path = await upload_image(processed_bytes, extension, content_type)

        await conn.execute(
            "update public.inventory_items set image_path=$2, updated_by=$3 where id=$1",
            item_id, new_path, user.id,
        )
        after = await conn.fetchrow(f"{_BASE_SELECT} where i.id = $1", item_id)
        await record_audit(conn, user.id, "item_image_changed", "inventory_item", str(item_id),
                            {"image_path": old_path}, {"image_path": new_path})

    if old_path:
        # Best-effort cleanup of the old file. Not part of the DB
        # transaction above (Storage isn't transactional with Postgres) -
        # if this fails, an orphaned old file is a minor storage-cost
        # issue, never a correctness or security one.
        await delete_image(old_path)

    result = await _attach_image_urls([_with_status(after)])
    return result[0]