from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.projects import router as projects_router
from app.api.routes.uploads import router as uploads_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.2.0")
app.include_router(health_router)
app.include_router(projects_router, prefix=settings.api_prefix)
app.include_router(uploads_router, prefix=settings.api_prefix)
