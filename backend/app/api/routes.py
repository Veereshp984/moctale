"""API route registrations."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"], summary="Health check")
def healthcheck() -> dict[str, str]:
    """Return a simple health status payload."""
    return {"status": "ok"}
