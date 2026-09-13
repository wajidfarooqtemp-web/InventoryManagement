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
    # Actually DELETE it, not just deactivate - a deactivated row still
    # blocks the unique-name check, so a merely-deactivated leftover from
    # a previous run would make every future run of this test fail with
    # 409, even though the code itself is behaving correctly.
    location_id = response.json()["id"]
    await client.delete(
        f"/api/v1/locations/{location_id}", headers={"Authorization": f"Bearer {admin_token}"},
    )


@pytest.mark.asyncio
async def test_kitchen_staff_can_read_inventory(client, kitchen_token):
    response = await client.get("/api/v1/inventory", headers={"Authorization": f"Bearer {kitchen_token}"})
    assert response.status_code == 200
    assert len(response.json()) > 0