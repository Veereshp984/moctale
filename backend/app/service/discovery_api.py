from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.service.discovery_clients import get_spotify_client, get_tmdb_client

logger = logging.getLogger(__name__)

discovery_router = APIRouter(prefix="/api", tags=["discovery"])


class MovieItem(BaseModel):
    id: str
    title: str
    poster: Optional[str] = None
    overview: Optional[str] = None
    popularity: Optional[float] = None


class MusicItem(BaseModel):
    id: str
    name: str
    albumArt: Optional[str] = None
    description: Optional[str] = None
    popularity: Optional[float] = None


IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


class _TTLCache:
    def __init__(self, ttl_seconds: int = 60) -> None:
        self.ttl = ttl_seconds
        self._store: Dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any:
        now = time.time()
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if now >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time() + self.ttl, value)


_cache: Optional[_TTLCache] = None


def _get_cache(settings: Optional[Settings] = None) -> _TTLCache:
    global _cache
    if _cache is None:
        settings = settings or get_settings()
        _cache = _TTLCache(ttl_seconds=settings.cache_ttl_seconds)
    return _cache


def _movie_dto(movie: Dict[str, Any]) -> MovieItem:
    poster_path = movie.get("poster_path")
    poster = f"{IMAGE_BASE}{poster_path}" if poster_path else None
    return MovieItem(
        id=str(movie.get("id")),
        title=movie.get("title") or movie.get("name") or "",
        poster=poster,
        overview=movie.get("overview"),
        popularity=float(movie.get("popularity", 0.0)) if movie.get("popularity") is not None else None,
    )


def _music_track_dto(track: Dict[str, Any]) -> MusicItem:
    images = (track.get("album") or {}).get("images") or []
    album_art = images[0]["url"] if images else None
    artists = ", ".join(a.get("name", "") for a in track.get("artists", []))
    return MusicItem(
        id=str(track.get("id")),
        name=track.get("name") or "",
        albumArt=album_art,
        description=artists or None,
        popularity=float(track.get("popularity", 0.0)) if track.get("popularity") is not None else None,
    )


def _music_album_dto(album: Dict[str, Any]) -> MusicItem:
    images = album.get("images") or []
    album_art = images[0]["url"] if images else None
    artists = ", ".join(a.get("name", "") for a in album.get("artists", []))
    return MusicItem(
        id=str(album.get("id")),
        name=album.get("name") or "",
        albumArt=album_art,
        description=artists or None,
        popularity=0.0,
    )


@discovery_router.get("/movies/search", response_model=List[MovieItem])
async def search_movies(query: str = Query(min_length=1), limit: int = Query(default=10, ge=1, le=50)) -> List[MovieItem]:
    settings = get_settings()
    if not settings.tmdb_api_key:
        raise HTTPException(status_code=503, detail="TMDb API not configured")
    cache = _get_cache(settings)
    cache_key = f"movies:search:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    client = get_tmdb_client(settings)
    try:
        results = await client.search_movies(query, limit=limit)
    except Exception as exc:  # pragma: no cover - maps known exceptions
        logger.exception("Movie search failed: %s", exc)
        raise HTTPException(status_code=502, detail="Upstream TMDb error") from exc
    items = [_movie_dto(m) for m in results]
    cache.set(cache_key, items)
    return items


@discovery_router.get("/movies/popular", response_model=List[MovieItem])
async def popular_movies(limit: int = Query(default=10, ge=1, le=50)) -> List[MovieItem]:
    settings = get_settings()
    if not settings.tmdb_api_key:
        raise HTTPException(status_code=503, detail="TMDb API not configured")
    cache = _get_cache(settings)
    cache_key = f"movies:popular:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    client = get_tmdb_client(settings)
    try:
        results = await client.popular_movies(limit=limit)
    except Exception as exc:
        logger.exception("Popular movies fetch failed: %s", exc)
        raise HTTPException(status_code=502, detail="Upstream TMDb error") from exc
    items = [_movie_dto(m) for m in results]
    cache.set(cache_key, items)
    return items


@discovery_router.get("/music/search", response_model=List[MusicItem])
async def search_music(query: str = Query(min_length=1), limit: int = Query(default=10, ge=1, le=50)) -> List[MusicItem]:
    settings = get_settings()
    if not (settings.spotify_client_id and settings.spotify_client_secret):
        raise HTTPException(status_code=503, detail="Spotify API not configured")
    cache = _get_cache(settings)
    cache_key = f"music:search:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    client = get_spotify_client(settings)
    try:
        tracks = await client.search_tracks(query, limit=limit)
    except Exception as exc:
        logger.exception("Music search failed: %s", exc)
        raise HTTPException(status_code=502, detail="Upstream Spotify error") from exc
    items = [_music_track_dto(t) for t in tracks]
    cache.set(cache_key, items)
    return items


@discovery_router.get("/music/popular", response_model=List[MusicItem])
async def popular_music(limit: int = Query(default=10, ge=1, le=50)) -> List[MusicItem]:
    settings = get_settings()
    if not (settings.spotify_client_id and settings.spotify_client_secret):
        raise HTTPException(status_code=503, detail="Spotify API not configured")
    cache = _get_cache(settings)
    cache_key = f"music:popular:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    client = get_spotify_client(settings)
    try:
        albums = await client.new_releases(limit=limit)
    except Exception as exc:
        logger.exception("Popular music fetch failed: %s", exc)
        raise HTTPException(status_code=502, detail="Upstream Spotify error") from exc
    items = [_music_album_dto(a) for a in albums]
    cache.set(cache_key, items)
    return items
