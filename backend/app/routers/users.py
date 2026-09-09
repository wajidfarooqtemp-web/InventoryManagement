"""
User management - admin only, per Section 19. Role/active changes are
kept as two separate small endpoints rather than one generic PATCH,
since they're conceptually different actions (who someone is vs whether
they can log in at all) and each deserves its own clear audit entry.
"""
from uuid import UUID
import httpx
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from app.database import get_pool
from app.dependencies import require_role
from app.security import CurrentUser
from app.schemas import UserOut, UserRoleUpdate, UserActiveUpdate, UserCreate
from app.audit import record_audit

router = APIRouter(prefix="/api/v1/users", tags=["users"])

_VALID_ROLES = ("kitchen_staff", "manager", "admin")


@router.get("", response_model=list[UserOut])
async def list_users(user: CurrentUser = Depends(require_role("admin"))):
    pool = get_pool()
    rows = await pool.fetch("select id, name, email, role, active from public.users order by name")
    return [dict(r) for r in rows]

@router.post("", response_model=UserOut, status_code=201)
async def create_user(body: UserCreate, user: CurrentUser = Depends(require_role("admin"))):
    """
    Creates a real login for a new person, without needing the Supabase
    dashboard at all. Calls Supabase's own Admin API (server-side, using
    the service-role key - never exposed to the frontend) to create the
    auth account; the Phase 1 database trigger then automatically creates
    the matching public.users row, which we simply read back afterward.
    """
    if body.role not in _VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(_VALID_ROLES)}")
    if "@" not in body.email:
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.supabase_url}/auth/v1/admin/users",
            headers={
                "Authorization": f"Bearer {settings.supabase_service_role_key}",
                "apikey": settings.supabase_service_role_key,
            },
            json={
                "email": body.email,
                "password": body.password,
                "email_confirm": True,  # internal, admin-created accounts - no verification email needed
                "user_metadata": {"name": body.name},
            },
        )

    if response.status_code not in (200, 201):
        # Supabase's own message (e.g. "email already exists") is safe to
        # pass through here - it's not internal system detail, it's a
        # normal validation-style response the admin needs to act on.
        detail = response.json().get("msg") or response.json().get("error_description") or "Could not create user."
        raise HTTPException(status_code=400, detail=detail)

    new_user_id = response.json()["id"]

    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        # The database trigger already inserted this row defaulted to
        # kitchen_staff - only need to change it if a different role was requested.
        if body.role != "kitchen_staff":
            await conn.execute("update public.users set role=$2 where id=$1", new_user_id, body.role)
        row = await conn.fetchrow("select id, name, email, role, active from public.users where id=$1", new_user_id)
        await record_audit(conn, user.id, "user_created", "user", str(new_user_id), None, dict(row))

    return dict(row)


@router.patch("/{user_id}/role", response_model=UserOut)
async def update_role(user_id: UUID, body: UserRoleUpdate, user: CurrentUser = Depends(require_role("admin"))):
    if body.role not in _VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(_VALID_ROLES)}")
    if str(user_id) == user.id and body.role != "admin":
        # Stops an admin accidentally locking themselves out with no
        # other admin around to undo it.
        raise HTTPException(status_code=400, detail="You cannot remove your own admin access.")

    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        before = await conn.fetchrow("select id, name, email, role, active from public.users where id=$1", user_id)
        if before is None:
            raise HTTPException(status_code=404, detail="User not found.")
        after = await conn.fetchrow(
            "update public.users set role=$2 where id=$1 returning id, name, email, role, active",
            user_id, body.role,
        )
        await record_audit(conn, user.id, "user_role_changed", "user", str(user_id), dict(before), dict(after))
    return dict(after)


@router.patch("/{user_id}/active", response_model=UserOut)
async def update_active(user_id: UUID, body: UserActiveUpdate, user: CurrentUser = Depends(require_role("admin"))):
    if str(user_id) == user.id and not body.active:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account.")

    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        before = await conn.fetchrow("select id, name, email, role, active from public.users where id=$1", user_id)
        if before is None:
            raise HTTPException(status_code=404, detail="User not found.")
        after = await conn.fetchrow(
            "update public.users set active=$2 where id=$1 returning id, name, email, role, active",
            user_id, body.active,
        )
        action = "user_reactivated" if body.active else "user_deactivated"
        await record_audit(conn, user.id, action, "user", str(user_id), dict(before), dict(after))
    return dict(after)