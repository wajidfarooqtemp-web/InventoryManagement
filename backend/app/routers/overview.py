"""
One aggregated endpoint for the dashboard, so the frontend makes a single
request instead of five. Deliberately its own simple query rather than
reusing activity.py's filterable one - overview only ever needs "the
latest N, no filters", so a leaner query is clearer here than bending a
more complex one to fit.
"""
from fastapi import APIRouter, Depends
from app.database import get_pool
from app.security import get_current_user, CurrentUser
from app.schemas import OverviewOut
from app.inventory_logic import calculate_status

router = APIRouter(prefix="/api/v1/overview", tags=["overview"])

# Higher severity sorts first, so the most urgent items are always at the
# top of "Needs Attention" regardless of when they were added.
_SEVERITY = {"OUT_OF_STOCK": 0, "CRITICAL": 1, "LOW": 2}


@router.get("", response_model=OverviewOut)
async def get_overview(user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        items = await conn.fetch(
            """
            select i.id, i.name, i.unit, i.current_stock, i.reorder_level, i.critical_level,
                   i.needs_confirmation, i.monthly_requirement, i.monthly_requirement_min,
                   i.monthly_requirement_max, l.name as location_name, c.name as category_name
            from public.inventory_items i
            join public.locations l on l.id = i.location_id
            join public.categories c on c.id = i.category_id
            where i.active = true
            """
        )
        total_locations = await conn.fetchval("select count(*) from public.locations where active = true")
        recent = await conn.fetch(
            """
            select m.id, m.item_id, i.name as item_name, l.name as location_name, m.period_id,
                   m.movement_type, m.quantity, m.resulting_stock, m.reason, m.related_transfer_id,
                   m.created_by, u.name as created_by_name, u.email as created_by_email, m.created_at
            from public.stock_movements m
            join public.inventory_items i on i.id = m.item_id
            join public.locations l on l.id = i.location_id
            left join public.users u on u.id = m.created_by
            where m.movement_type != 'OPENING_BALANCE'
            order by m.created_at desc
            limit 15
            """
        )

    counts = {"GOOD": 0, "LOW": 0, "CRITICAL": 0, "OUT_OF_STOCK": 0}
    needs_attention = []
    needs_confirmation_count = 0

    for item in items:
        status = calculate_status(item["current_stock"], item["reorder_level"], item["critical_level"])
        counts[status] += 1
        if item["needs_confirmation"]:
            needs_confirmation_count += 1
        if status != "GOOD":
            needs_attention.append({
                "item_id": item["id"],
                "item_name": item["name"],
                "location_name": item["location_name"],
                "category_name": item["category_name"],
                "unit": item["unit"],
                "current_stock": float(item["current_stock"]),
                "monthly_requirement": item["monthly_requirement"],
                "monthly_requirement_min": item["monthly_requirement_min"],
                "monthly_requirement_max": item["monthly_requirement_max"],
                "status": status,
            })

    needs_attention.sort(key=lambda x: (_SEVERITY[x["status"]], x["item_name"]))

    return {
        "total_active_items": len(items),
        "total_locations": total_locations,
        "items_good": counts["GOOD"],
        "items_low": counts["LOW"],
        "items_critical": counts["CRITICAL"],
        "items_out_of_stock": counts["OUT_OF_STOCK"],
        "items_needs_confirmation": needs_confirmation_count,
        "needs_attention": needs_attention[:25],
        "recent_activity": [dict(r) for r in recent],
    }