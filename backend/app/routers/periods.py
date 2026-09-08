"""
Read-only endpoints for monthly periods and the "what happened to X in
month Y" report. Periods themselves are only ever CREATED by the stock
engine (Phase 4, periods.py) - nothing here writes anything.
"""
from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_pool
from app.security import get_current_user, CurrentUser
from app.schemas import PeriodOut, PeriodItemSummaryOut
from app.period_reports import get_period_summary

router = APIRouter(prefix="/api/v1/periods", tags=["periods"])


def _with_is_current(row) -> dict:
    today = date.today()
    d = dict(row)
    d["is_current"] = (d["year"] == today.year and d["month"] == today.month)
    return d


@router.get("", response_model=list[PeriodOut])
async def list_periods(user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    rows = await pool.fetch(
        "select id, year, month, status from public.inventory_periods order by year desc, month desc"
    )
    return [_with_is_current(r) for r in rows]


@router.get("/{period_id}/items/{item_id}/summary", response_model=PeriodItemSummaryOut)
async def get_item_period_summary(period_id: UUID, item_id: UUID, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        item = await conn.fetchrow(
            """
            select i.name as item_name, i.unit, l.name as location_name,
                   i.monthly_requirement, i.monthly_requirement_min, i.monthly_requirement_max
            from public.inventory_items i
            join public.locations l on l.id = i.location_id
            where i.id = $1
            """,
            item_id,
        )
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found.")

        if not await conn.fetchval("select 1 from public.inventory_periods where id = $1", period_id):
            raise HTTPException(status_code=404, detail="Period not found.")

        summary = await get_period_summary(conn, period_id, item_id)

    return {"period_id": period_id, "item_id": item_id, **dict(item), **summary}