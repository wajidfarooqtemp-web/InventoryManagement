"""
Confirms role enforcement holds at the API layer, not just hidden in the
UI (Section 19) - the actual security boundary the plan requires.
"""
import pytest


@pytest.mark.asyncio
async def test_kitchen_staff_cannot_create_location(client, kitchen_token):
    response = await client.post(
        "/api/v1/locations", headers={"Authorization": f"Bearer {kitchen_token}"},
        json={"name": "RBAC Test Location"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_create_location(client, admin_token):
    response = await client.post(
        "/api/v1/locations", headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "RBAC Test Location Admin"},
    )
    assert response.status_code == 201
    # Clean up - tests shouldn't leave real-looking data behind.
    location_id = response.json()["id"]
    await client.patch(
        f"/api/v1/locations/{location_id}", headers={"Authorization": f"Bearer {admin_token}"},
        json={"active": False},
    )


@pytest.mark.asyncio
async def test_kitchen_staff_can_read_inventory(client, kitchen_token):
    response = await client.get("/api/v1/inventory", headers={"Authorization": f"Bearer {kitchen_token}"})
    assert response.status_code == 200
    assert len(response.json()) > 0