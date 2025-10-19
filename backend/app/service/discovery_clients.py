from __future__ import annotations

import asyncio
import base64
import logging
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    pass


class TMDbClient:
    def __init__(self, api_key: str, api_base: str = "https://api.themoviedb.org/3") -> None:
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.api_base, timeout=10.0)

    async def _request(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params.copy() if params else {}
        params["api_key"] = self.api_key
        # Basic 429 handling with single retry
        for attempt in range(2):
            resp = await self._client.get(path, params=params)
            if resp.status_code == 429 and attempt == 0:
                retry_after = resp.headers.get("Retry-After")
                delay = min(1.0, float(retry_after)) if retry_after else 0.2
                logger.warning("TMDb rate limited, retrying after %.2fs", delay)
                await asyncio.sleep(delay)
                continue
            if resp.status_code >= 400:
                logger.error("TMDb error %s: %s", resp.status_code, resp.text)
                resp.raise_for_status()
            return resp.json()
        raise RateLimitError("TMDb rate limit exceeded")

    async def search_movies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        data = await self._request("/search/movie", params={"query": query, "page": 1})
        results = data.get("results", [])
        return results[:limit]

    async def popular_movies(self, limit: int = 10) -> List[Dict[str, Any]]:
        data = await self._request("/movie/popular", params={"page": 1})
        results = data.get("results", [])
        return results[:limit]


class SpotifyClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str = "https://accounts.spotify.com/api/token",
        api_base: str = "https://api.spotify.com/v1",
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.api_base = api_base.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.api_base, timeout=10.0)
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0
        self._lock = asyncio.Lock()

    async def _fetch_access_token(self) -> None:
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "client_credentials"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(self.token_url, headers=headers, data=data)
        if resp.status_code >= 400:
            logger.error("Spotify token fetch failed %s: %s", resp.status_code, resp.text)
            resp.raise_for_status()
        payload = resp.json()
        self._token = payload.get("access_token")
        expires_in = int(payload.get("expires_in", 3600))
        # Renew a bit earlier than expiry
        self._token_expiry = time.time() + max(30, int(expires_in * 0.9))
        logger.info("Fetched new Spotify access token")

    async def _ensure_token(self) -> None:
        if self._token and time.time() < self._token_expiry:
            return
        async with self._lock:
            if self._token and time.time() < self._token_expiry:
                return
            await self._fetch_access_token()

    async def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        await self._ensure_token()
        headers = {"Authorization": f"Bearer {self._token}"}
        for attempt in range(3):
            resp = await self._client.request(method, path, params=params, headers=headers)
            if resp.status_code == 401 and attempt == 0:
                # token expired/invalid -> refresh and retry once
                logger.info("Spotify token expired, refreshing and retrying")
                await self._fetch_access_token()
                headers["Authorization"] = f"Bearer {self._token}"
                continue
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                delay = min(1.0, float(retry_after)) if retry_after else 0.2
                logger.warning("Spotify rate limited, retrying after %.2fs", delay)
                await asyncio.sleep(delay)
                continue
            if resp.status_code >= 400:
                logger.error("Spotify API error %s: %s", resp.status_code, resp.text)
                resp.raise_for_status()
            return resp.json()
        raise RateLimitError("Spotify rate limit exceeded")

    async def search_tracks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        data = await self._request("GET", "/search", params={"q": query, "type": "track", "limit": limit})
        items = data.get("tracks", {}).get("items", [])
        return items

    async def new_releases(self, limit: int = 10) -> List[Dict[str, Any]]:
        data = await self._request("GET", "/browse/new-releases", params={"limit": limit})
        items = data.get("albums", {}).get("items", [])
        return items


@lru_cache()
def get_tmdb_client(settings: Optional[Settings] = None) -> TMDbClient:
    settings = settings or get_settings()
    return TMDbClient(api_key=settings.tmdb_api_key, api_base=settings.tmdb_api_base)


@lru_cache()
def get_spotify_client(settings: Optional[Settings] = None) -> SpotifyClient:
    settings = settings or get_settings()
    return SpotifyClient(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        token_url=settings.spotify_token_url,
        api_base=settings.spotify_api_base,
    )
