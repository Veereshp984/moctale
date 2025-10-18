"""External content discovery integrations for TMDb and Spotify."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, Hashable, TypeVar

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
_SPOTIFY_AUTH_PATH = "/api/token"
_SPOTIFY_SEARCH_PATH = "/v1/search"
_SPOTIFY_NEW_RELEASES_PATH = "/v1/browse/new-releases"


class DiscoveryServiceError(RuntimeError):
    """Base error for discovery service failures."""

    def __init__(self, message: str, *, provider: str | None = None) -> None:
        super().__init__(message)
        self.provider = provider


class RateLimitError(DiscoveryServiceError):
    """Raised when an upstream provider indicates a rate limit has been exceeded."""

    def __init__(self, message: str, *, provider: str | None = None, retry_after: float | None = None) -> None:
        super().__init__(message, provider=provider)
        self.retry_after = retry_after


T = TypeVar("T")


class TTLCache(Generic[T]):
    """Thread-safe in-memory TTL cache for lightweight response caching."""

    def __init__(self, ttl_seconds: float, *, time_func: Callable[[], float] | None = None) -> None:
        self._ttl = ttl_seconds
        self._time = time_func or time.monotonic
        self._lock = threading.Lock()
        self._values: dict[Hashable, tuple[float, T]] = {}

    def get(self, key: Hashable) -> T | None:
        with self._lock:
            entry = self._values.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at <= self._time():
                self._values.pop(key, None)
                return None
            return value

    def set(self, key: Hashable, value: T) -> None:
        with self._lock:
            self._values[key] = (self._time() + self._ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._values.clear()


class MovieSummary(BaseModel):
    id: str
    title: str
    overview: str | None = None
    release_date: str | None = None
    language: str | None = Field(default=None, description="Original language code")
    popularity: float | None = None
    poster_url: str | None = None
    vote_average: float | None = None
    vote_count: int | None = None


class MovieCollection(BaseModel):
    page: int
    total_pages: int
    total_results: int
    items: list[MovieSummary]


class MovieSearchResults(MovieCollection):
    query: str


class MusicSummary(BaseModel):
    id: str
    name: str
    artists: list[str]
    album: str | None = None
    preview_url: str | None = None
    external_url: str | None = None
    image_url: str | None = None
    popularity: int | None = None
    source: str | None = Field(default=None, description="Originating entity type (track, album, playlist)")


class MusicCollection(BaseModel):
    total: int | None = None
    limit: int | None = None
    offset: int | None = None
    items: list[MusicSummary]


class MusicSearchResults(MusicCollection):
    query: str


def _safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass
class TMDbClient:
    api_key: str
    client: httpx.Client | None = None
    base_url: str = "https://api.themoviedb.org/3"
    _owns_client: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        if not self.api_key:
            msg = "TMDb API key must be provided"
            raise ValueError(msg)
        if self.client is None:
            self.client = httpx.Client(base_url=self.base_url, timeout=10.0)
            self._owns_client = True
        else:
            self._owns_client = False

    def close(self) -> None:
        if self._owns_client and self.client is not None:
            self.client.close()

    def _get(self, path: str, params: Dict[str, Any]) -> dict[str, Any]:
        if self.client is None:
            msg = "HTTP client not initialised"
            raise DiscoveryServiceError(msg, provider="tmdb")
        query = {"api_key": self.api_key}
        query.update({k: v for k, v in params.items() if v is not None})
        try:
            response = self.client.get(path, params=query)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                retry_after_header = exc.response.headers.get("Retry-After")
                retry_after = float(retry_after_header) if retry_after_header else None
                raise RateLimitError("TMDb rate limit exceeded", provider="tmdb", retry_after=retry_after) from exc
            logger.exception("TMDb request failed with status %s", exc.response.status_code)
            raise DiscoveryServiceError("TMDb request failed", provider="tmdb") from exc
        except httpx.HTTPError as exc:
            logger.exception("TMDb request failed: %s", exc)
            raise DiscoveryServiceError("TMDb request failed", provider="tmdb") from exc
        try:
            payload = response.json()
        except ValueError as exc:
            logger.exception("TMDb response payload could not be decoded")
            raise DiscoveryServiceError("Unexpected TMDb response", provider="tmdb") from exc
        if not isinstance(payload, dict) or not payload:
            logger.error("TMDb response payload missing or invalid structure")
            raise DiscoveryServiceError("Unexpected TMDb response", provider="tmdb")
        return payload

    def search_movies(self, query: str, *, language: str | None = "en-US", page: int = 1) -> MovieSearchResults:
        payload = self._get("/search/movie", {"query": query, "language": language, "page": page})
        items = [self._parse_movie(entry) for entry in payload.get("results", [])]
        return MovieSearchResults(
            query=query,
            page=_safe_int(payload.get("page"), 1) or 1,
            total_pages=_safe_int(payload.get("total_pages"), 1) or 1,
            total_results=_safe_int(payload.get("total_results"), len(items)) or len(items),
            items=items,
        )

    def get_popular_movies(
        self,
        *,
        language: str | None = "en-US",
        region: str | None = None,
        page: int = 1,
    ) -> MovieCollection:
        payload = self._get("/movie/popular", {"language": language, "region": region, "page": page})
        items = [self._parse_movie(entry) for entry in payload.get("results", [])]
        return MovieCollection(
            page=_safe_int(payload.get("page"), 1) or 1,
            total_pages=_safe_int(payload.get("total_pages"), 1) or 1,
            total_results=_safe_int(payload.get("total_results"), len(items)) or len(items),
            items=items,
        )

    @staticmethod
    def _parse_movie(entry: dict[str, Any]) -> MovieSummary:
        poster_path = entry.get("poster_path")
        poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else None
        return MovieSummary(
            id=str(entry.get("id")),
            title=entry.get("title") or entry.get("name") or "",
            overview=entry.get("overview"),
            release_date=entry.get("release_date"),
            language=entry.get("original_language"),
            popularity=entry.get("popularity"),
            poster_url=poster_url,
            vote_average=entry.get("vote_average"),
            vote_count=_safe_int(entry.get("vote_count")),
        )


class SpotifyClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        token_client: httpx.Client | None = None,
        api_client: httpx.Client | None = None,
        auth_base_url: str = "https://accounts.spotify.com",
        api_base_url: str = "https://api.spotify.com",
        time_func: Callable[[], float] | None = None,
    ) -> None:
        if not client_id or not client_secret:
            msg = "Spotify credentials must be provided"
            raise ValueError(msg)
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_client = token_client or httpx.Client(base_url=auth_base_url, timeout=10.0)
        self._api_client = api_client or httpx.Client(base_url=api_base_url, timeout=10.0)
        self._time = time_func or time.monotonic
        self._token_lock = threading.Lock()
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0
        self._token_margin = 30.0

    def close(self) -> None:
        self._token_client.close()
        self._api_client.close()

    def _get_access_token(self, *, force: bool = False) -> str:
        with self._token_lock:
            now = self._time()
            if force or self._access_token is None or now >= self._token_expires_at:
                logger.debug("Refreshing Spotify access token")
                self._refresh_access_token()
            return self._access_token  # type: ignore[return-value]

    def _refresh_access_token(self) -> None:
        auth = httpx.BasicAuth(self._client_id, self._client_secret)
        try:
            response = self._token_client.post(
                _SPOTIFY_AUTH_PATH,
                data={"grant_type": "client_credentials"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                auth=auth,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.exception("Spotify token request failed with status %s", exc.response.status_code)
            raise DiscoveryServiceError("Spotify authentication failed", provider="spotify") from exc
        except httpx.HTTPError as exc:
            logger.exception("Spotify token request failed: %s", exc)
            raise DiscoveryServiceError("Spotify authentication failed", provider="spotify") from exc
        payload = response.json()
        if not isinstance(payload, dict) or "access_token" not in payload:
            logger.error("Spotify token payload malformed: %s", payload)
            raise DiscoveryServiceError("Spotify authentication failed", provider="spotify")
        access_token = payload["access_token"]
        expires_in = float(payload.get("expires_in", 3600))
        now = self._time()
        self._access_token = access_token
        self._token_expires_at = now + max(expires_in - self._token_margin, 5.0)
        logger.debug("Obtained Spotify token expiring at %.0f", self._token_expires_at)

    def _api_request(self, method: str, path: str, *, params: Dict[str, Any] | None = None) -> dict[str, Any]:
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = self._api_client.request(method, path, params=params, headers=headers)
            if response.status_code == 401:
                logger.info("Spotify token rejected, forcing refresh")
                token = self._get_access_token(force=True)
                headers["Authorization"] = f"Bearer {token}"
                response = self._api_client.request(method, path, params=params, headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                retry_after_header = exc.response.headers.get("Retry-After")
                retry_after = float(retry_after_header) if retry_after_header else None
                raise RateLimitError("Spotify rate limit exceeded", provider="spotify", retry_after=retry_after) from exc
            logger.exception("Spotify request failed with status %s", exc.response.status_code)
            raise DiscoveryServiceError("Spotify request failed", provider="spotify") from exc
        except httpx.HTTPError as exc:
            logger.exception("Spotify request failed: %s", exc)
            raise DiscoveryServiceError("Spotify request failed", provider="spotify") from exc
        try:
            payload = response.json()
        except ValueError as exc:
            logger.exception("Spotify response payload could not be decoded")
            raise DiscoveryServiceError("Unexpected Spotify response", provider="spotify") from exc
        if not isinstance(payload, dict):
            logger.error("Spotify response payload malformed")
            raise DiscoveryServiceError("Unexpected Spotify response", provider="spotify")
        return payload

    def search_tracks(self, query: str, *, limit: int = 10, market: str = "US") -> MusicSearchResults:
        payload = self._api_request(
            "GET",
            _SPOTIFY_SEARCH_PATH,
            params={"q": query, "type": "track", "limit": limit, "market": market},
        )
        tracks = payload.get("tracks", {})
        items = [self._parse_track(item) for item in tracks.get("items", [])]
        return MusicSearchResults(
            query=query,
            total=_safe_int(tracks.get("total")),
            limit=_safe_int(tracks.get("limit")),
            offset=_safe_int(tracks.get("offset")),
            items=items,
        )

    def get_popular_tracks(self, *, limit: int = 10, market: str = "US") -> MusicCollection:
        payload = self._api_request(
            "GET",
            _SPOTIFY_NEW_RELEASES_PATH,
            params={"limit": limit, "market": market},
        )
        albums = payload.get("albums", {})
        items = [self._parse_album(album) for album in albums.get("items", [])]
        return MusicCollection(
            total=_safe_int(albums.get("total")),
            limit=_safe_int(albums.get("limit")),
            offset=_safe_int(albums.get("offset")),
            items=items,
        )

    @staticmethod
    def _parse_track(entry: dict[str, Any]) -> MusicSummary:
        album = entry.get("album") or {}
        images = album.get("images") or []
        image_url = images[0].get("url") if images else None
        external_urls = entry.get("external_urls") or {}
        return MusicSummary(
            id=entry.get("id", ""),
            name=entry.get("name", ""),
            artists=[artist.get("name", "") for artist in entry.get("artists", [])],
            album=album.get("name"),
            preview_url=entry.get("preview_url"),
            external_url=external_urls.get("spotify"),
            image_url=image_url,
            popularity=_safe_int(entry.get("popularity")),
            source="track",
        )

    @staticmethod
    def _parse_album(entry: dict[str, Any]) -> MusicSummary:
        images = entry.get("images") or []
        image_url = images[0].get("url") if images else None
        external_urls = entry.get("external_urls") or {}
        return MusicSummary(
            id=entry.get("id", ""),
            name=entry.get("name", ""),
            artists=[artist.get("name", "") for artist in entry.get("artists", [])],
            album=entry.get("name"),
            preview_url=None,
            external_url=external_urls.get("spotify"),
            image_url=image_url,
            popularity=_safe_int(entry.get("popularity")),
            source=entry.get("album_type") or "album",
        )


class ContentDiscoveryService:
    """Facade combining TMDb and Spotify integrations with light caching."""

    def __init__(
        self,
        tmdb_client: TMDbClient,
        spotify_client: SpotifyClient,
        *,
        popular_ttl_seconds: float = 300.0,
        cache_time_func: Callable[[], float] | None = None,
    ) -> None:
        self._tmdb = tmdb_client
        self._spotify = spotify_client
        self._popular_cache: TTLCache[Any] = TTLCache(popular_ttl_seconds, time_func=cache_time_func)

    def search_movies(self, query: str, *, language: str | None = "en-US", page: int = 1) -> MovieSearchResults:
        logger.debug("Searching TMDb movies for query '%s'", query)
        return self._tmdb.search_movies(query, language=language, page=page)

    def popular_movies(
        self,
        *,
        limit: int = 10,
        language: str | None = "en-US",
        region: str | None = None,
    ) -> MovieCollection:
        cache_key = ("popular_movies", limit, language, region)
        cached = self._popular_cache.get(cache_key)
        if cached is not None:
            logger.debug("Serving popular movies from cache for key %s", cache_key)
            return cached.model_copy(deep=True)
        collection = self._tmdb.get_popular_movies(language=language, region=region)
        limited_items = collection.items[:limit]
        result = MovieCollection(
            page=collection.page,
            total_pages=collection.total_pages,
            total_results=collection.total_results,
            items=limited_items,
        )
        self._popular_cache.set(cache_key, result)
        return result

    def search_music(self, query: str, *, limit: int = 10, market: str = "US") -> MusicSearchResults:
        logger.debug("Searching Spotify tracks for query '%s'", query)
        return self._spotify.search_tracks(query, limit=limit, market=market)

    def popular_music(self, *, limit: int = 10, market: str = "US") -> MusicCollection:
        cache_key = ("popular_music", limit, market)
        cached = self._popular_cache.get(cache_key)
        if cached is not None:
            logger.debug("Serving popular music from cache for key %s", cache_key)
            return cached.model_copy(deep=True)
        collection = self._spotify.get_popular_tracks(limit=limit, market=market)
        self._popular_cache.set(cache_key, collection)
        return collection


__all__ = [
    "ContentDiscoveryService",
    "DiscoveryServiceError",
    "MusicCollection",
    "MusicSearchResults",
    "MusicSummary",
    "RateLimitError",
    "TMDbClient",
    "MovieCollection",
    "MovieSearchResults",
    "MovieSummary",
    "SpotifyClient",
]
