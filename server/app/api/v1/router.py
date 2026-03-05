"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.routes import auth, files, health

router = APIRouter(prefix="/v1")
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(files.router)
