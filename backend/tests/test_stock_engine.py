"""
Proves the two hardest guarantees in the whole system actually hold: a
duplicated request never double-applies, and two simultaneous requests
against the same item never lose an update.
"""
import asyncio
import uuid
import pytest


async def _get_rice_id(client, token):
    response = await client.get("/api/v1/inventory?q=Rice", headers={"Authorization": f"Bearer {token}"})
    return response.json()[0]["id"]


@pytest.mark.asyncio
async def test_idempotent_receive_does_not_double_apply(client, kitchen_token):
    item_id = await _get_rice_id(client, kitchen_token)
    key = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {kitchen_token}"}

    first = await client.post(f"/api/v1/inventory/{item_id}/receive", headers=headers,
                               json={"quantity": 7, "idempotency_key": key})
    second = await client.post(f"/api/v1/inventory/{item_id}/receive", headers=headers,
                                json={"quantity": 7, "idempotency_key": key})

    assert first.json()["current_stock"] == second.json()["current_stock"]


@pytest.mark.asyncio
async def test_concurrent_use_does_not_lose_an_update(client, kitchen_token):
    item_id = await _get_rice_id(client, kitchen_token)
    headers = {"Authorization": f"Bearer {kitchen_token}"}

    before = await client.get(f"/api/v1/inventory/{item_id}", headers=headers)
    starting_stock = before.json()["current_stock"]

    results = await asyncio.gather(
        client.post(f"/api/v1/inventory/{item_id}/use", headers=headers,
                    json={"quantity": 1, "idempotency_key": str(uuid.uuid4())}),
        client.post(f"/api/v1/inventory/{item_id}/use", headers=headers,
                    json={"quantity": 2, "idempotency_key": str(uuid.uuid4())}),
    )
    assert all(r.status_code == 200 for r in results)

    after = await client.get(f"/api/v1/inventory/{item_id}", headers=headers)
    assert after.json()["current_stock"] == starting_stock - 3