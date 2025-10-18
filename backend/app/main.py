"""FastAPI application entrypoint."""

from fastapi import FastAPI

from .api import router as api_router
from .core.config import settings


def create_application() -> FastAPI:
    """Instantiate the FastAPI application with configured routes."""
    application = FastAPI(
        title=settings.project_name,
        version=settings.version,
    )

    @application.get("/", tags=["Root"], summary="Service root")
    def read_root() -> dict[str, str]:
        return {"message": f"Welcome to {settings.project_name}"}

    application.include_router(api_router, prefix=settings.api_prefix)
    return application


app = create_application()
