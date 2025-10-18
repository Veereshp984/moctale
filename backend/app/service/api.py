"""FastAPI service exposing recommendation endpoints."""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.model.recommender import RecommendationService
from app.service.discovery import (
    ContentDiscoveryService,
    DiscoveryServiceError,
    MovieCollection,
    MovieSearchResults,
    MusicCollection,
    MusicSearchResults,
    RateLimitError,
    SpotifyClient,
    TMDbClient,
)

BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_ROOT = BASE_DIR.parent
DEFAULT_MODEL_DIR = BACKEND_ROOT / "models" / "latest"

logger = logging.getLogger(__name__)

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


@lru_cache()
def _discovery_service_factory(tmdb_api_key: str, spotify_client_id: str, spotify_client_secret: str) -> ContentDiscoveryService:
    tmdb_client = TMDbClient(api_key=tmdb_api_key)
    spotify_client = SpotifyClient(client_id=spotify_client_id, client_secret=spotify_client_secret)
    return ContentDiscoveryService(tmdb_client=tmdb_client, spotify_client=spotify_client)


def get_discovery_service() -> ContentDiscoveryService:
    tmdb_api_key = os.getenv("TMDB_API_KEY")
    spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
    spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not tmdb_api_key or not spotify_client_id or not spotify_client_secret:
        raise HTTPException(status_code=503, detail="Content discovery credentials unavailable")
    try:
        return _discovery_service_factory(tmdb_api_key, spotify_client_id, spotify_client_secret)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="Invalid discovery service configuration") from exc


def _map_discovery_error(exc: DiscoveryServiceError) -> HTTPException:
    provider_key = (exc.provider or "external provider").lower()
    provider_label_map = {"tmdb": "TMDb", "spotify": "Spotify"}
    provider_label = provider_label_map.get(provider_key, (exc.provider or "External provider").replace("_", " ").title())
    logger.warning("Discovery provider error from %s: %s", provider_label, exc)
    if isinstance(exc, RateLimitError):
        detail = f"{provider_label} rate limit exceeded"
        headers: dict[str, str] | None = None
        if exc.retry_after is not None:
            retry_after_value: float | int | str = exc.retry_after
            if isinstance(retry_after_value, float) and retry_after_value.is_integer():
                retry_after_value = int(retry_after_value)
            headers = {"Retry-After": str(retry_after_value)}
        return HTTPException(status_code=429, detail=detail, headers=headers)
    return HTTPException(status_code=503, detail=f"{provider_label} service unavailable")


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


@app.get("/discovery/movies/popular", response_model=MovieCollection)
def get_popular_movies(
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of movies to return"),
    language: str | None = Query(
        default="en-US",
        min_length=2,
        max_length=5,
        description="Preferred language code used by TMDb",
    ),
    region: str | None = Query(
        default=None,
        min_length=2,
        max_length=2,
        description="ISO 3166-1 region code to bias popularity",
    ),
    service: ContentDiscoveryService = Depends(get_discovery_service),
) -> MovieCollection:
    try:
        normalised_region = region.upper() if region else None
        return service.popular_movies(limit=limit, language=language, region=normalised_region)
    except DiscoveryServiceError as exc:
        raise _map_discovery_error(exc) from exc


@app.get("/discovery/movies/search", response_model=MovieSearchResults)
def search_movies(
    query: str = Query(..., min_length=1, max_length=200, description="Search term for TMDb"),
    page: int = Query(default=1, ge=1, le=50, description="TMDb results page"),
    language: str | None = Query(
        default="en-US",
        min_length=2,
        max_length=5,
        description="Preferred language code used by TMDb",
    ),
    service: ContentDiscoveryService = Depends(get_discovery_service),
) -> MovieSearchResults:
    try:
        return service.search_movies(query=query, language=language, page=page)
    except DiscoveryServiceError as exc:
        raise _map_discovery_error(exc) from exc


@app.get("/discovery/music/popular", response_model=MusicCollection)
def get_popular_music(
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of music items to return"),
    market: str = Query(default="US", min_length=2, max_length=2, description="Spotify market code"),
    service: ContentDiscoveryService = Depends(get_discovery_service),
) -> MusicCollection:
    try:
        return service.popular_music(limit=limit, market=market.upper())
    except DiscoveryServiceError as exc:
        raise _map_discovery_error(exc) from exc


@app.get("/discovery/music/search", response_model=MusicSearchResults)
def search_music(
    query: str = Query(..., min_length=1, max_length=200, description="Spotify search term"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of tracks to return"),
    market: str = Query(default="US", min_length=2, max_length=2, description="Spotify market code"),
    service: ContentDiscoveryService = Depends(get_discovery_service),
) -> MusicSearchResults:
    try:
        return service.search_music(query=query, limit=limit, market=market.upper())
    except DiscoveryServiceError as exc:
        raise _map_discovery_error(exc) from exc
