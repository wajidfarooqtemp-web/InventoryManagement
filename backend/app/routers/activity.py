"""
Two read-only views over the same stock_movements table: one scoped to a
single item (its full history), one global across everything (the
manager/CEO activity feed) - both support the filters described in the
architecture doc's Section 20.
"""
from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from app.database import get_pool
from app.security import get_current_user, CurrentUser
from app.schemas import MovementOut

router = APIRouter(prefix="/api/v1", tags=["activity"])

# Shared by both endpoints below so a movement always carries the same
# readable item/location/user names, regardless of which view is asking.
_MOVEMENT_SELECT = """
    select m.*, i.name as item_name, l.name as location_name,
           u.name as created_by_name, u.email as created_by_email
    from public.stock_movements m
    join public.inventory_items i on i.id = m.item_id
    join public.locations l on l.id = i.location_id
    left join public.users u on u.id = m.created_by
"""


def _build_filters(period_id, date_from, date_to, movement_type, item_id=None, location_id=None, user_id=None):
    """
    Builds a WHERE clause and its matching parameter list together, so the
    two can never drift out of sync. All values stay parameterized - only
    the column names/placeholders are built as text.
    """
    clauses, params = [], []

    def add(sql_fragment: str, value):
        params.append(value)
        clauses.append(sql_fragment.format(len(params)))

    if item_id is not None:
        add("m.item_id = ${}", item_id)
    if location_id is not None:
        add("i.location_id = ${}", location_id)
    if user_id is not None:
        add("m.created_by = ${}", user_id)
    if period_id is not None:
        add("m.period_id = ${}", period_id)
    if movement_type is not None:
        add("m.movement_type = ${}", movement_type.upper())
    if date_from is not None:
        add("m.created_at >= ${}", date_from)
    if date_to is not None:
        add("m.created_at <= ${}", date_to)

    where_sql = f"where {' and '.join(clauses)}" if clauses else ""
    return where_sql, params


@router.get("/inventory/{item_id}/history", response_model=list[MovementOut])
async def get_item_history(
    item_id: UUID,
    period_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    movement_type: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    user: CurrentUser = Depends(get_current_user),
):
    pool = get_pool()
    where_sql, params = _build_filters(period_id, date_from, date_to, movement_type, item_id=item_id)
    params += [limit, offset]
    rows = await pool.fetch(
        f"{_MOVEMENT_SELECT} {where_sql} order by m.created_at desc limit ${len(params)-1} offset ${len(params)}",
        *params,
    )
    return [dict(r) for r in rows]


@router.get("/activity", response_model=list[MovementOut])
async def get_global_activity(
    location_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    period_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    movement_type: Optional[str] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    user: CurrentUser = Depends(get_current_user),
):
    pool = get_pool()
    where_sql, params = _build_filters(period_id, date_from, date_to, movement_type, location_id=location_id, user_id=user_id)
    params += [limit, offset]
    rows = await pool.fetch(
        f"{_MOVEMENT_SELECT} {where_sql} order by m.created_at desc limit ${len(params)-1} offset ${len(params)}",
        *params,
    )
    return [dict(r) for r in rows]