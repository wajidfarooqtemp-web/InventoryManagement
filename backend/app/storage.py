"""
Thin wrapper around Supabase Storage's REST API, using the service-role
key (server-side only, never sent to the frontend). Uses httpx directly
rather than the full supabase-py client since this is the only Storage
feature we need.
"""
import httpx
from uuid import uuid4
from fastapi import HTTPException
from app.config import settings

_BUCKET = "item-images"


def _headers():
    # Supabase Storage's REST API requires BOTH headers, even for the
    # service-role key - Authorization alone silently fails. This was
    # the actual cause of every upload returning "could not save the
    # image" regardless of file size or type.
    return {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
    }


async def upload_image(processed_bytes: bytes, extension: str, content_type: str) -> str:
    """Random UUID filename - never the user's original filename (Section 29:
    prevents path traversal and filename-based attacks)."""
    path = f"{uuid4()}.{extension}"
    url = f"{settings.supabase_url}/storage/v1/object/{_BUCKET}/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers={**_headers(), "Content-Type": content_type}, content=processed_bytes)
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail="Could not save the image. Please try again.")
    return path


async def sign_url(path: str, expires_in: int = 3600) -> str | None:
    """Bucket is private - the frontend only ever gets this short-lived
    signed URL, never a raw/public bucket URL."""
    url = f"{settings.supabase_url}/storage/v1/object/sign/{_BUCKET}/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=_headers(), json={"expiresIn": expires_in})
    if response.status_code != 200:
        return None
    signed_path = response.json().get("signedURL")
    return f"{settings.supabase_url}/storage/v1{signed_path}" if signed_path else None


async def delete_image(path: str):
    url = f"{settings.supabase_url}/storage/v1/object/{_BUCKET}/{path}"
    async with httpx.AsyncClient() as client:
        await client.delete(url, headers=_headers())