import asyncpg


async def create_category(
    conn: asyncpg.Connection, *, name: str, slug: str, schema: str
):
    query = f"""
        INSERT INTO {schema}.categories (name, slug)
        VALUES ($1, $2)
        RETURNING id, name, slug, created_at
    """
    return await conn.fetchrow(query, name, slug)


async def list_categories(conn: asyncpg.Connection, *, schema: str):
    query = f"""
        SELECT id, name, slug, created_at
        FROM {schema}.categories
        ORDER BY name ASC
    """
    return await conn.fetch(query)
