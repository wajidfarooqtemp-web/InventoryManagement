"""
Categories: same read/write rules as locations - see that file's comment.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_pool
from app.security import get_current_user, CurrentUser
from app.dependencies import require_role
from app.schemas import CategoryOut, CategoryCreate, CategoryUpdate
from app.audit import record_audit

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(active: Optional[bool] = True, user: CurrentUser = Depends(get_current_user)):
    """
    Defaults to active-only, so deprecated categories (Section above -
    the old Food/Spices/Dairy/Cooking Oil split) disappear from normal
    dropdowns without deleting their history. Pass ?active=false to see
    only the deprecated ones (used by the admin management screen).
    """
    pool = get_pool()
    rows = await pool.fetch("select id, name, active from public.categories where active = $1 order by name", active)
    return [dict(r) for r in rows]


@router.post("", response_model=CategoryOut, status_code=201)
async def create_category(body: CategoryCreate, user: CurrentUser = Depends(require_role("manager", "admin"))):
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        if await conn.fetchval("select id from public.categories where name = $1", body.name):
            raise HTTPException(status_code=409, detail="A category with this name already exists.")
        row = await conn.fetchrow(
            "insert into public.categories (name) values ($1) returning id, name, active",
            body.name,
        )
        await record_audit(conn, user.id, "category_created", "category", str(row["id"]), None, dict(row))
    return dict(row)

@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: UUID, user: CurrentUser = Depends(require_role("admin"))):
    """
    A real, permanent delete - not a soft-deactivate. Only allowed when no
    item references this category at all (active or inactive), since an
    item pointing at a deleted category_id would break every query that
    joins against it. Deactivating remains the right move for "we don't
    use this anymore but items still reference it."
    """
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        before = await conn.fetchrow("select id, name, active from public.categories where id=$1", category_id)
        if before is None:
            raise HTTPException(status_code=404, detail="Category not found.")

        item_count = await conn.fetchval(
            "select count(*) from public.inventory_items where category_id=$1", category_id
        )
        if item_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete - {item_count} item(s) still use this category. Reassign or deactivate them first.",
            )

        await conn.execute("delete from public.categories where id=$1", category_id)
        await record_audit(conn, user.id, "category_deleted", "category", str(category_id), dict(before), None)
@router.patch("/{category_id}", response_model=CategoryOut)
async def update_category(category_id: str, body: CategoryUpdate, user: CurrentUser = Depends(require_role("manager", "admin"))):
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        before = await conn.fetchrow("select id, name, active from public.categories where id = $1", category_id)
        if before is None:
            raise HTTPException(status_code=404, detail="Category not found.")

        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(before)

        set_clauses = ", ".join(f"{key} = ${i+2}" for i, key in enumerate(updates.keys()))
        row = await conn.fetchrow(
            f"update public.categories set {set_clauses} where id = $1 returning id, name, active",
            category_id, *updates.values(),
        )
        await record_audit(conn, user.id, "category_updated", "category", category_id, dict(before), dict(row))
    return dict(row)