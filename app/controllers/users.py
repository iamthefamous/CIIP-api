from typing import Optional

import asyncpg

from app.ciip_api.schemas.users import AudienceType, UserRole


async def upsert_user(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    email: Optional[str],
    full_name: Optional[str],
    role: UserRole,
    audience_type: Optional[AudienceType],
    schema: str,
):
    query = f"""
        INSERT INTO {schema}.users (id, email, full_name, role, audience_type)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (id) DO UPDATE
        SET email = EXCLUDED.email,
            full_name = EXCLUDED.full_name,
            role = EXCLUDED.role,
            audience_type = EXCLUDED.audience_type,
            updated_at = now()
        RETURNING id, email, full_name, role, audience_type, created_at, updated_at
    """
    return await conn.fetchrow(query, user_id, email, full_name, role, audience_type)


async def get_user(conn: asyncpg.Connection, *, user_id: str, schema: str):
    query = f"""
        SELECT id, email, full_name, role, audience_type, created_at, updated_at
        FROM {schema}.users
        WHERE id = $1
    """
    return await conn.fetchrow(query, user_id)
