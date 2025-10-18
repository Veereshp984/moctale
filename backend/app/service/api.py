"""FastAPI service exposing recommendation endpoints."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.model.recommender import RecommendationService

BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_ROOT = BASE_DIR.parent
DEFAULT_MODEL_DIR = BACKEND_ROOT / "models" / "latest"

app = FastAPI(title="Soundwave Recommendation Service", version="1.0.0")


class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: list[str]
    fallback_used: bool


@lru_cache()
def _service_factory(model_dir: str) -> RecommendationService:
    return RecommendationService(model_dir)


def get_service() -> RecommendationService:
    model_dir = Path(os.getenv("RECOMMENDER_MODEL_DIR", str(DEFAULT_MODEL_DIR))).resolve()
    try:
        return _service_factory(str(model_dir))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Model artifacts unavailable") from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/recommendations/{user_id}", response_model=RecommendationResponse)
def get_recommendations(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=100, description="Number of recommendations to return"),
    service: RecommendationService = Depends(get_service),
) -> RecommendationResponse:
    try:
        recommendations, fallback_used = service.recommend_for_user(user_id, limit)
    except Exception as exc:  # noqa: BLE001 - surface predictable error payload
        raise HTTPException(status_code=500, detail="Recommendation inference failed") from exc
    if not recommendations:
        raise HTTPException(status_code=404, detail="No recommendations available")
    return RecommendationResponse(user_id=user_id, recommendations=recommendations, fallback_used=fallback_used)
