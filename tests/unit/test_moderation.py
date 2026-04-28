import uuid

import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_moderator_can_approve(client):
    institution_user_id = uuid.uuid4()
    institution_headers = auth_headers(
        institution_user_id,
        "institution@example.com",
        role="institution",
    )
    await client.post(
        "/v1/users/me",
        headers=institution_headers,
        json={"full_name": "Inst User", "audience_type": "general_public"},
    )

    admin_headers = auth_headers(uuid.uuid4(), "admin@example.com", role="admin")
    await client.post(
        "/v1/users/me",
        headers=admin_headers,
        json={"full_name": "Admin", "audience_type": "general_public"},
    )

    category_resp = await client.post(
        "/v1/categories",
        headers=admin_headers,
        json={"name": "Events", "slug": "events"},
    )
    category_id = category_resp.json()["id"]

    institution_resp = await client.post(
        "/v1/institutions",
        headers=institution_headers,
        json={
            "name": "Youth Center",
            "description": "Community events",
            "website": "https://example.org",
        },
    )
    institution_id = institution_resp.json()["id"]

    opportunity_resp = await client.post(
        "/v1/opportunities",
        headers=institution_headers,
        json={
            "title": "Community Meetup",
            "description": "Monthly meetup.",
            "opportunity_type": "event",
            "category_id": category_id,
            "institution_id": institution_id,
            "audiences": ["general_public"],
        },
    )
    opportunity_id = opportunity_resp.json()["id"]

    moderator_headers = auth_headers(
        uuid.uuid4(), "moderator@example.com", role="moderator"
    )
    await client.post(
        "/v1/users/me",
        headers=moderator_headers,
        json={"full_name": "Moderator", "audience_type": "general_public"},
    )

    approve_resp = await client.post(
        "/v1/moderation/approve",
        headers=moderator_headers,
        json={"opportunity_id": opportunity_id, "note": "Looks good"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    list_resp = await client.get(
        "/v1/opportunities",
        headers=moderator_headers,
        params={"status": "approved", "limit": 10, "offset": 0},
    )
    assert list_resp.status_code == 200
    payload = list_resp.json()
    assert payload["items"][0]["status"] == "approved"
