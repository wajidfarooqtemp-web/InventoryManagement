"""
Shared test fixtures. Logs in as two real, already-existing Supabase test
accounts (one kitchen_staff, one admin) so tests exercise the REAL JWT
verification path end to end - not a mocked one. These tests run against
your actual dev database, so never point TEST_* credentials at anything
you consider production data.
"""
import os
import httpx
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]


async def _login(email: str, password: str) -> str:
    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={"apikey": SUPABASE_ANON_KEY},
            json={"email": email, "password": password},
        )
        response.raise_for_status()
        return response.json()["access_token"]


@pytest_asyncio.fixture
async def kitchen_token():
    return await _login(os.environ["TEST_KITCHEN_EMAIL"], os.environ["TEST_KITCHEN_PASSWORD"])


@pytest_asyncio.fixture
async def admin_token():
    return await _login(os.environ["TEST_ADMIN_EMAIL"], os.environ["TEST_ADMIN_PASSWORD"])


@pytest_asyncio.fixture
async def client():
    # In-process ASGI transport - runs the real app (real DB pool, real
    # JWT verification) without needing a separately running server.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        async with app.router.lifespan_context(app):
            yield c