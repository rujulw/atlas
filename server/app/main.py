"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.core.config import settings


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.get("/", tags=["meta"])
    async def root() -> dict[str, str]:
        return {"service": settings.PROJECT_NAME, "status": "scaffolded"}

    return app


app = create_application()
