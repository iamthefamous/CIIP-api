from typing import Optional

import asyncpg

from app.ciip_api.schemas.opportunities import OpportunityStatus


async def list_queue(
    conn: asyncpg.Connection, *, schema: str, status: OpportunityStatus, limit: int, offset: int
):
    query = f"""
        SELECT id, opportunity_id, status, reviewed_by, note, created_at, reviewed_at
        FROM {schema}.moderation_queue
        WHERE status = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
    """
    rows = await conn.fetch(query, status, limit, offset)
    total = await conn.fetchval(
        f"SELECT count(*) FROM {schema}.moderation_queue WHERE status = $1", status
    )
    return total, rows


async def update_queue_status(
    conn: asyncpg.Connection,
    *,
    schema: str,
    opportunity_id: str,
    reviewed_by: str,
    status: OpportunityStatus,
    note: Optional[str],
):
    query = f"""
        UPDATE {schema}.moderation_queue
        SET status = $1,
            reviewed_by = $2,
            note = $3,
            reviewed_at = now()
        WHERE opportunity_id = $4
        RETURNING id, opportunity_id, status, reviewed_by, note, created_at, reviewed_at
    """
    return await conn.fetchrow(query, status, reviewed_by, note, opportunity_id)
