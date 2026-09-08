"""
Receive, Use, Adjust, Transfer - the four ways stock actually changes.
Kitchen staff can Receive/Use; only manager/admin can Adjust (it always
needs a reason - it's how a mistake gets corrected without editing
history) or Transfer between locations.
"""
from uuid import UUID
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request
from app.rate_limit import limiter
from pydantic import BaseModel, Field
from app.database import get_pool
from app.security import get_current_user, CurrentUser
from app.dependencies import require_role
from app.stock_engine import create_movement
from app.inventory_logic import calculate_status
from app.audit import record_audit

router = APIRouter(prefix="/api/v1/inventory", tags=["stock movements"])


class ReceiveOrUseRequest(BaseModel):
    quantity: float = Field(gt=0)
    idempotency_key: str = Field(min_length=1, max_length=100)


class AdjustRequest(BaseModel):
    quantity: float = Field(gt=0)  # magnitude only - direction is separate below
    direction: Literal["increase", "decrease"]
    reason: str = Field(min_length=3, max_length=500)
    idempotency_key: str = Field(min_length=1, max_length=100)


class TransferRequest(BaseModel):
    to_item_id: UUID
    quantity: float = Field(gt=0)
    idempotency_key: str = Field(min_length=1, max_length=100)


async def _item_with_status(conn, item_id):
    row = await conn.fetchrow(
        "select id, current_stock, reorder_level, critical_level from public.inventory_items where id=$1",
        item_id,
    )
    return {
        "item_id": row["id"],
        "current_stock": float(row["current_stock"]),
        "status": calculate_status(row["current_stock"], row["reorder_level"], row["critical_level"]),
    }


@router.post("/{item_id}/receive")
@limiter.limit("30/minute")
async def receive_stock(request: Request, item_id: UUID, body: ReceiveOrUseRequest, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        movement, _ = await create_movement(conn, item_id, "RECEIVE", body.quantity, user.id, body.idempotency_key)
        result = await _item_with_status(conn, item_id)
    return {"movement": movement, **result}


@router.post("/{item_id}/use")
@limiter.limit("30/minute")
async def use_stock(request: Request, item_id: UUID, body: ReceiveOrUseRequest, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        movement, _ = await create_movement(conn, item_id, "USE", body.quantity, user.id, body.idempotency_key)
        result = await _item_with_status(conn, item_id)
    return {"movement": movement, **result}


@router.post("/{item_id}/adjust")
@limiter.limit("20/minute")
async def adjust_stock(request: Request, item_id: UUID, body: AdjustRequest, user: CurrentUser = Depends(require_role("manager", "admin"))):
    pool = get_pool()
    signed_quantity = body.quantity if body.direction == "increase" else -body.quantity
    async with pool.acquire() as conn, conn.transaction():
        movement, _ = await create_movement(
            conn, item_id, "ADJUSTMENT", signed_quantity, user.id, body.idempotency_key, reason=body.reason
        )
        result = await _item_with_status(conn, item_id)
        await record_audit(conn, user.id, "stock_adjusted", "inventory_item", str(item_id),
                            None, {"quantity": signed_quantity, "reason": body.reason})
    return {"movement": movement, **result}


@router.post("/{item_id}/transfer")
@limiter.limit("20/minute")
async def transfer_stock(request: Request, item_id: UUID, body: TransferRequest, user: CurrentUser = Depends(require_role("manager", "admin"))):
    """
    One transfer = two linked movements (OUT on the source item, IN on the
    destination item) in ONE transaction - both happen or neither does.
    The destination must be a real, existing item at another location
    (we don't guess a match by name - too easy to send stock to the wrong
    place on a typo).
    """
    if item_id == body.to_item_id:
        raise HTTPException(status_code=400, detail="Cannot transfer an item to itself.")

    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        if not await conn.fetchval("select 1 from public.inventory_items where id=$1 and active=true", body.to_item_id):
            raise HTTPException(status_code=400, detail="Destination item not found or inactive.")

        out_movement, _ = await create_movement(
            conn, item_id, "TRANSFER_OUT", body.quantity, user.id, f"{body.idempotency_key}-out"
        )
        in_movement, _ = await create_movement(
            conn, body.to_item_id, "TRANSFER_IN", body.quantity, user.id, f"{body.idempotency_key}-in",
            related_transfer_id=out_movement["id"],
        )
        await conn.execute(
            "update public.stock_movements set related_transfer_id=$1 where id=$2",
            in_movement["id"], out_movement["id"],
        )
        source = await _item_with_status(conn, item_id)
        destination = await _item_with_status(conn, body.to_item_id)

    return {"out_movement": out_movement, "in_movement": in_movement, "source": source, "destination": destination}