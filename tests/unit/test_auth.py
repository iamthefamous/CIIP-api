import uuid

import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_requires_auth(client):
    response = await client.get("/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_moderation_requires_role(client):
    headers = auth_headers(uuid.uuid4(), "user@example.com", role="user")
    response = await client.get("/v1/moderation/queue", headers=headers)
    assert response.status_code == 403
