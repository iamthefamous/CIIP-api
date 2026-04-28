import uuid

import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_create_and_filter_opportunities(client):
    institution_user_id = uuid.uuid4()
    headers = auth_headers(institution_user_id, "institution@example.com", role="institution")
    await client.post(
        "/v1/users/me",
        headers=headers,
        json={"full_name": "Inst User", "audience_type": "general_public"},
    )

    category_resp = await client.post(
        "/v1/categories",
        headers=headers,
        json={"name": "Internships", "slug": "internships"},
    )
    assert category_resp.status_code == 201
    category_id = category_resp.json()["id"]

    institution_resp = await client.post(
        "/v1/institutions",
        headers=headers,
        json={
            "name": "Innovation Hub",
            "description": "Youth innovation lab",
            "website": "https://example.org",
        },
    )
    assert institution_resp.status_code == 201
    institution_id = institution_resp.json()["id"]

    opportunity_resp = await client.post(
        "/v1/opportunities",
        headers=headers,
        json={
            "title": "Summer Internship",
            "description": "Learn and build projects.",
            "opportunity_type": "internship",
            "category_id": category_id,
            "institution_id": institution_id,
            "audiences": ["high_schoolers"],
            "location": "Bishkek",
            "url": "https://example.org/intern",
        },
    )
    assert opportunity_resp.status_code == 201
    opportunity_id = opportunity_resp.json()["id"]
    assert opportunity_resp.json()["status"] == "pending"

    moderator_headers = auth_headers(uuid.uuid4(), "moderator@example.com", role="moderator")
    await client.post(
        "/v1/users/me",
        headers=moderator_headers,
        json={"full_name": "Moderator", "audience_type": "general_public"},
    )

    list_resp = await client.get(
        "/v1/opportunities",
        headers=moderator_headers,
        params={
            "status": "pending",
            "audience": "high_schoolers",
            "opportunity_type": "internship",
            "limit": 10,
            "offset": 0,
        },
    )
    assert list_resp.status_code == 200
    payload = list_resp.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == opportunity_id
