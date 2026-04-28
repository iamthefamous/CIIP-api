import os
import uuid

import asyncpg
import pytest
import pytest_asyncio
from httpx import AsyncClient
from jose import jwt

from app.main import create_app
from app.utils.config import get_settings
from app.utils.db import init_connection


@pytest.fixture(scope="session", autouse=True)
def configure_env() -> None:
    os.environ.setdefault("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
    os.environ.setdefault("APP_SCHEMA", "ciip_test")
    os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret")
    os.environ.setdefault("SUPABASE_AUDIENCE", "authenticated")


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest_asyncio.fixture(scope="session")
async def db_pool(settings):
    pool = await asyncpg.create_pool(
        dsn=settings.postgres_url,
        init=lambda conn: init_connection(conn, settings.app_schema),
    )
    yield pool
    await pool.close()


@pytest_asyncio.fixture(autouse=True)
async def clear_db(db_pool, settings):
    tables = [
        "saved_opportunities",
        "opportunity_audiences",
        "moderation_queue",
        "opportunities",
        "categories",
        "institutions",
        "users",
    ]
    async with db_pool.acquire() as conn:
        await conn.execute(
            "TRUNCATE TABLE "
            + ", ".join(f"{settings.app_schema}.{table}" for table in tables)
            + " CASCADE"
        )
    yield


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


def make_token(user_id: uuid.UUID, email: str, role: str) -> str:
    secret = os.environ["SUPABASE_JWT_SECRET"]
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "aud": os.environ.get("SUPABASE_AUDIENCE", "authenticated"),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def auth_headers(user_id: uuid.UUID, email: str, role: str = "user") -> dict:
    token = make_token(user_id, email, role)
    return {"Authorization": f"Bearer {token}"}
