"""
A guessed/nonexistent ID must return a plain 404 - never information
that could help someone enumerate real records (Section 32).
"""
import uuid
import pytest


@pytest.mark.asyncio
async def test_nonexistent_item_returns_404(client, kitchen_token):
    fake_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/inventory/{fake_id}", headers={"Authorization": f"Bearer {kitchen_token}"})
    assert response.status_code == 404