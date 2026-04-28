from typing import Optional

import asyncpg
from fastapi import FastAPI

from app.utils.config import Settings


async def init_connection(conn: asyncpg.Connection, schema: str) -> None:
    await conn.execute(f"SET search_path TO {schema}")


async def init_pool(app: FastAPI, settings: Settings) -> None:
    pool = await asyncpg.create_pool(
        dsn=settings.postgres_url,
        init=lambda conn: init_connection(conn, settings.app_schema),
    )
    app.state.pool = pool


async def close_pool(app: FastAPI) -> None:
    pool: Optional[asyncpg.Pool] = getattr(app.state, "pool", None)
    if pool:
        await pool.close()
