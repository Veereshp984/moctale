from __future__ import annotations

from importlib import reload
from typing import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def api_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    # Provide default env so app starts
    monkeypatch.setenv("TMDB_API_KEY", "test_tmdb")
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "id")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "secret")

    from app.service import api, discovery_clients, discovery_api

    # Reset cached clients and cache
    discovery_clients.get_spotify_client.cache_clear()
    discovery_clients.get_tmdb_client.cache_clear()
    discovery_api._cache = None  # type: ignore[attr-defined]

    reload(api)
    client = TestClient(api.app)
    try:
        yield client
    finally:
        discovery_clients.get_spotify_client.cache_clear()
        discovery_clients.get_tmdb_client.cache_clear()
        discovery_api._cache = None  # type: ignore[attr-defined]


def make_response(status_code: int = 200, json: dict | None = None, headers: dict | None = None) -> httpx.Response:
    return httpx.Response(status_code=status_code, json=json or {}, headers=headers or {})


async def _no_call(*args, **kwargs):  # pragma: no cover - safety
    raise AssertionError("Unexpected HTTP call during test")


def test_movies_search_happy_path_and_cache(api_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # Track calls
    calls = {"get": 0}

    async def fake_get(self: httpx.AsyncClient, url: str, params: dict | None = None, **kwargs):
        calls["get"] += 1
        assert url == "/search/movie"
        assert params and params.get("api_key")
        data = {
            "results": [
                {"id": 1, "title": "Movie A", "poster_path": "/p1.jpg", "overview": "A", "popularity": 5.5},
                {"id": 2, "title": "Movie B", "poster_path": None, "overview": "B", "popularity": 4.2},
            ]
        }
        return make_response(json=data)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    # First call hits upstream
    r1 = api_client.get("/api/movies/search", params={"query": "batman", "limit": 2})
    assert r1.status_code == 200
    payload1 = r1.json()
    assert len(payload1) == 2
    assert payload1[0]["title"] == "Movie A"
    assert payload1[0]["poster"].endswith("/p1.jpg")

    # Second call served from cache
    r2 = api_client.get("/api/movies/search", params={"query": "batman", "limit": 2})
    assert r2.status_code == 200
    payload2 = r2.json()
    assert payload2 == payload1
    assert calls["get"] == 1


def test_spotify_search_handles_token_refresh(api_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    token_calls = {"post": 0}
    request_calls = {"req": 0}

    async def fake_post(self: httpx.AsyncClient, url: str, **kwargs):
        token_calls["post"] += 1
        assert "api/token" in url
        token = "token1" if token_calls["post"] == 1 else "token2"
        return make_response(json={"access_token": token, "token_type": "Bearer", "expires_in": 3600})

    async def fake_request(self: httpx.AsyncClient, method: str, url: str, params=None, headers=None, **kwargs):
        request_calls["req"] += 1
        assert url == "/search"
        if request_calls["req"] == 1:
            # Simulate expired token
            return make_response(status_code=401, json={})
        # Success on retry
        return make_response(
            json={
                "tracks": {
                    "items": [
                        {
                            "id": "t1",
                            "name": "Song 1",
                            "popularity": 88,
                            "album": {"images": [{"url": "https://img/cover.jpg"}]},
                            "artists": [{"name": "Artist"}],
                        }
                    ]
                }
            }
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)
    # Prevent TMDb accidental calls
    monkeypatch.setattr(httpx.AsyncClient, "get", _no_call)

    resp = api_client.get("/api/music/search", params={"query": "test", "limit": 1})
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["id"] == "t1"
    assert items[0]["albumArt"].startswith("https://img/")
    assert token_calls["post"] == 2
    assert request_calls["req"] == 2


def test_tmdb_rate_limit_retry_on_popular(api_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"get": 0}

    async def fake_get(self: httpx.AsyncClient, url: str, params: dict | None = None, **kwargs):
        calls["get"] += 1
        assert url == "/movie/popular"
        if calls["get"] == 1:
            return make_response(status_code=429, json={}, headers={"Retry-After": "0"})
        return make_response(json={"results": [{"id": 9, "title": "P", "popularity": 3.14}]})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    r = api_client.get("/api/movies/popular", params={"limit": 1})
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert calls["get"] == 2


def test_missing_query_returns_422(api_client: TestClient) -> None:
    r = api_client.get("/api/movies/search")
    assert r.status_code == 422
