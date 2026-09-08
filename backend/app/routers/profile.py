"""
One endpoint the frontend calls right after login to find out who's
logged in and what they can do. Doubles as a smoke test for the whole
chain: Supabase login -> JWT -> FastAPI verification -> users table lookup.
"""
from fastapi import APIRouter, Depends
from app.security import get_current_user, CurrentUser
from app.dependencies import require_role

router = APIRouter(prefix="/api/v1", tags=["profile"])


@router.get("/me")
def get_my_profile(user: CurrentUser = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role}


# Temporary - proves require_role actually blocks non-admins. Safe to
# remove once real admin-only routes exist in later phases.
@router.get("/admin-check")
def admin_check(user: CurrentUser = Depends(require_role("admin"))):
    return {"message": f"Hello {user.name}, you have admin access."}