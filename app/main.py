from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI

from app.ciip_api.routers.v1 import (
    categories,
    institutions,
    moderation,
    opportunities,
    saved,
    users,
)
from app.utils.config import get_settings
from app.utils.db import close_pool, init_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await init_pool(app, settings)
    if settings.redis_url:
        app.state.redis = redis.from_url(settings.redis_url, decode_responses=True)
    yield
    if getattr(app.state, "redis", None):
        await app.state.redis.close()
    await close_pool(app)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
    app.include_router(users.router, prefix="/v1")
    app.include_router(categories.router, prefix="/v1")
    app.include_router(institutions.router, prefix="/v1")
    app.include_router(opportunities.router, prefix="/v1")
    app.include_router(moderation.router, prefix="/v1")
    app.include_router(saved.router, prefix="/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
