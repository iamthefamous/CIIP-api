from typing import Optional

import asyncpg


async def create_institution(
    conn: asyncpg.Connection,
    *,
    name: str,
    description: Optional[str],
    website: Optional[str],
    owner_user_id: str,
    schema: str,
):
    query = f"""
        INSERT INTO {schema}.institutions (name, description, website, owner_user_id)
        VALUES ($1, $2, $3, $4)
        RETURNING id, name, description, website, is_verified, owner_user_id, created_at, updated_at
    """
    return await conn.fetchrow(query, name, description, website, owner_user_id)


async def list_institutions(
    conn: asyncpg.Connection, *, schema: str, limit: int, offset: int
):
    query = f"""
        SELECT id, name, description, website, is_verified, owner_user_id, created_at, updated_at
        FROM {schema}.institutions
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
    """
    rows = await conn.fetch(query, limit, offset)
    total = await conn.fetchval(f"SELECT count(*) FROM {schema}.institutions")
    return total, rows


async def verify_institution(
    conn: asyncpg.Connection, *, schema: str, institution_id: str, is_verified: bool
):
    query = f"""
        UPDATE {schema}.institutions
        SET is_verified = $1,
            updated_at = now()
        WHERE id = $2
        RETURNING id, name, description, website, is_verified, owner_user_id, created_at, updated_at
    """
    return await conn.fetchrow(query, is_verified, institution_id)
