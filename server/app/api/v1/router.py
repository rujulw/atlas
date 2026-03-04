"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.routes import health

router = APIRouter(prefix="/v1")
router.include_router(health.router)
