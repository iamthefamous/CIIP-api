import asyncpg


async def save_opportunity(
    conn: asyncpg.Connection, *, schema: str, user_id: str, opportunity_id: str
):
    query = f"""
        INSERT INTO {schema}.saved_opportunities (user_id, opportunity_id)
        VALUES ($1, $2)
        ON CONFLICT (user_id, opportunity_id) DO UPDATE
        SET saved_at = saved_opportunities.saved_at
        RETURNING user_id, opportunity_id, saved_at
    """
    return await conn.fetchrow(query, user_id, opportunity_id)


async def unsave_opportunity(
    conn: asyncpg.Connection, *, schema: str, user_id: str, opportunity_id: str
):
    query = f"""
        DELETE FROM {schema}.saved_opportunities
        WHERE user_id = $1 AND opportunity_id = $2
    """
    await conn.execute(query, user_id, opportunity_id)


async def list_saved(
    conn: asyncpg.Connection, *, schema: str, user_id: str, limit: int, offset: int
):
    query = f"""
        SELECT opportunity_id, saved_at
        FROM {schema}.saved_opportunities
        WHERE user_id = $1
        ORDER BY saved_at DESC
        LIMIT $2 OFFSET $3
    """
    rows = await conn.fetch(query, user_id, limit, offset)
    total = await conn.fetchval(
        f"SELECT count(*) FROM {schema}.saved_opportunities WHERE user_id = $1", user_id
    )
    return total, rows
