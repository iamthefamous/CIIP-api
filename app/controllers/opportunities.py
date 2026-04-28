from __future__ import annotations

from typing import Iterable, Optional

import asyncpg

from app.ciip_api.schemas.opportunities import OpportunityStatus, OpportunityType
from app.ciip_api.schemas.users import AudienceType


async def create_opportunity(
    conn: asyncpg.Connection,
    *,
    schema: str,
    title: str,
    description: str,
    opportunity_type: OpportunityType,
    category_id: str,
    institution_id: str,
    submitted_by: str,
    status: OpportunityStatus,
    deadline: Optional[str],
    location: Optional[str],
    url: Optional[str],
    audiences: Iterable[AudienceType],
    ai_tags: Optional[list],
    ai_summary: Optional[str],
):
    insert_opportunity = f"""
        INSERT INTO {schema}.opportunities (
            title, description, opportunity_type, category_id, institution_id,
            submitted_by, status, deadline, location, url, ai_tags, ai_summary
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING id, title, description, opportunity_type, category_id, institution_id,
                  submitted_by, status, deadline, location, url, ai_tags, ai_summary,
                  created_at, updated_at
    """
    async with conn.transaction():
        row = await conn.fetchrow(
            insert_opportunity,
            title,
            description,
            opportunity_type,
            category_id,
            institution_id,
            submitted_by,
            status,
            deadline,
            location,
            url,
            ai_tags,
            ai_summary,
        )
        if audiences:
            await conn.executemany(
                f"""
                    INSERT INTO {schema}.opportunity_audiences (opportunity_id, audience)
                    VALUES ($1, $2)
                """,
                [(row["id"], audience) for audience in audiences],
            )
        await conn.execute(
            f"""
                INSERT INTO {schema}.moderation_queue (opportunity_id, status)
                VALUES ($1, $2)
            """,
            row["id"],
            status,
        )
        opportunity = await get_opportunity(conn, schema=schema, opportunity_id=row["id"])
    return opportunity


async def list_opportunities(
    conn: asyncpg.Connection,
    *,
    schema: str,
    status: OpportunityStatus,
    limit: int,
    offset: int,
    opportunity_type: Optional[OpportunityType],
    category_id: Optional[str],
    audiences: Optional[list[AudienceType]],
):
    base_from = f"""
        FROM {schema}.opportunities o
        JOIN {schema}.categories c ON c.id = o.category_id
        JOIN {schema}.institutions i ON i.id = o.institution_id
        LEFT JOIN {schema}.opportunity_audiences oa ON oa.opportunity_id = o.id
    """
    conditions = ["o.status = $1"]
    params = [status]
    param_index = 2

    if opportunity_type:
        conditions.append(f"o.opportunity_type = ${param_index}")
        params.append(opportunity_type)
        param_index += 1
    if category_id:
        conditions.append(f"o.category_id = ${param_index}")
        params.append(category_id)
        param_index += 1
    if audiences:
        conditions.append(f"oa.audience = ANY(${param_index})")
        params.append(audiences)
        param_index += 1

    where_clause = " AND ".join(conditions)

    count_query = f"SELECT count(DISTINCT o.id) {base_from} WHERE {where_clause}"
    total = await conn.fetchval(count_query, *params)

    query = f"""
        SELECT o.id, o.title, o.description, o.opportunity_type, o.category_id,
               o.institution_id, o.submitted_by, o.status, o.deadline, o.location,
               o.url, o.ai_tags, o.ai_summary, o.created_at, o.updated_at,
               COALESCE(array_agg(DISTINCT oa.audience) FILTER (WHERE oa.audience IS NOT NULL), '{{}}')
                   AS audiences
        {base_from}
        WHERE {where_clause}
        GROUP BY o.id
        ORDER BY o.created_at DESC
        LIMIT ${param_index} OFFSET ${param_index + 1}
    """
    rows = await conn.fetch(query, *params, limit, offset)
    return total, rows


async def get_opportunity(conn: asyncpg.Connection, *, schema: str, opportunity_id: str):
    query = f"""
        SELECT o.id, o.title, o.description, o.opportunity_type, o.category_id,
               o.institution_id, o.submitted_by, o.status, o.deadline, o.location,
               o.url, o.ai_tags, o.ai_summary, o.created_at, o.updated_at,
               COALESCE(array_agg(DISTINCT oa.audience) FILTER (WHERE oa.audience IS NOT NULL), '{{}}')
                   AS audiences
        FROM {schema}.opportunities o
        LEFT JOIN {schema}.opportunity_audiences oa ON oa.opportunity_id = o.id
        WHERE o.id = $1
        GROUP BY o.id
    """
    return await conn.fetchrow(query, opportunity_id)


async def update_opportunity_status(
    conn: asyncpg.Connection, *, schema: str, opportunity_id: str, status: OpportunityStatus
):
    query = f"""
        UPDATE {schema}.opportunities
        SET status = $1,
            updated_at = now()
        WHERE id = $2
        RETURNING id, title, description, opportunity_type, category_id, institution_id,
                  submitted_by, status, deadline, location, url, ai_tags, ai_summary,
                  created_at, updated_at
    """
    return await conn.fetchrow(query, status, opportunity_id)
