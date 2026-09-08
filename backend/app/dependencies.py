"""
Role-based access control, built on top of get_current_user.

Usage on any route:
    @router.post("/inventory", dependencies=[Depends(require_role("manager", "admin"))])

This is the ONE place role-checking logic lives, so every protected route
enforces it identically - never by hiding a button in the frontend
(that would only be cosmetic, not real security).
"""
from fastapi import Depends, HTTPException, status
from app.security import get_current_user, CurrentUser


def require_role(*allowed_roles: str):
    def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to perform this action.",
            )
        return user
    return checker