from __future__ import annotations

from fastapi import APIRouter, HTTPException
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import AsyncSessionFactory

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready() -> dict[str, str]:
    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        redis = Redis.from_url(settings.redis_url)
        try:
            await redis.ping()
        finally:
            await redis.aclose()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Dependency unavailable: {exc}") from exc
    return {"status": "ready"}
