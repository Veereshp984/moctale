"""Unit tests for TMDb and Spotify discovery integrations."""
from __future__ import annotations

from typing import Any

import httpx

from app.service.discovery import (
    ContentDiscoveryService,
    MovieCollection,
    MovieSearchResults,
    MovieSummary,
    MusicCollection,
    MusicSearchResults,
    MusicSummary,
    SpotifyClient,
    TMDbClient,
)


def test_tmdb_client_maps_movie_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/search/movie"
        assert request.url.params["api_key"] == "test-key"
        assert request.url.params["query"] == "blade"
        return httpx.Response(
            200,
            json={
                "page": 1,
                "total_pages": 5,
                "total_results": 100,
                "results": [
                    {
                        "id": 42,
                        "title": "Blade Runner",
                        "overview": "Neo-noir sci-fi.",
                        "poster_path": "/blade.jpg",
                        "release_date": "1982-06-25",
                        "original_language": "en",
                        "vote_average": 8.4,
                        "vote_count": 12987,
                        "popularity": 45.3,
                    }
                ],
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(base_url="https://api.themoviedb.org/3", transport=transport)
    tmdb_client = TMDbClient(api_key="test-key", client=client)

    results = tmdb_client.search_movies("blade")

    assert results.query == "blade"
    assert results.total_pages == 5
    assert len(results.items) == 1
    movie = results.items[0]
    assert movie.id == "42"
    assert movie.poster_url == "https://image.tmdb.org/t/p/w500/blade.jpg"
    assert movie.vote_count == 12987
    assert movie.release_date == "1982-06-25"


def test_spotify_client_refreshes_expired_tokens() -> None:
    token_requests: list[httpx.Request] = []
    authorization_headers: list[str] = []
    current_time = [0.0]

    def token_handler(request: httpx.Request) -> httpx.Response:
        token_requests.append(request)
        return httpx.Response(200, json={"access_token": f"token-{len(token_requests)}", "expires_in": 60})

    def api_handler(request: httpx.Request) -> httpx.Response:
        authorization_headers.append(request.headers["Authorization"])
        return httpx.Response(
            200,
            json={
                "tracks": {
                    "items": [
                        {
                            "id": "track-123",
                            "name": "Echo",
                            "artists": [{"name": "Nova"}],
                            "album": {"name": "Echoes", "images": [{"url": "https://img"}]},
                            "preview_url": "https://preview",
                            "external_urls": {"spotify": "https://open.spotify.com/track/track-123"},
                            "popularity": 87,
                        }
                    ],
                    "total": 1,
                    "limit": 1,
                    "offset": 0,
                }
            },
        )

    token_client = httpx.Client(base_url="https://accounts.spotify.com", transport=httpx.MockTransport(token_handler))
    api_client = httpx.Client(base_url="https://api.spotify.com", transport=httpx.MockTransport(api_handler))
    spotify_client = SpotifyClient(
        "client-id",
        "client-secret",
        token_client=token_client,
        api_client=api_client,
        time_func=lambda: current_time[0],
    )

    first = spotify_client.search_tracks("ambient", limit=1)
    assert first.items[0].id == "track-123"

    current_time[0] = 40.0
    second = spotify_client.search_tracks("ambient", limit=1)
    assert second.items[0].id == "track-123"

    assert authorization_headers == ["Bearer token-1", "Bearer token-2"]
    assert len(token_requests) == 2


def test_content_discovery_service_caches_popular_results() -> None:
    movie = MovieSummary(id="m-1", title="Synthwave", overview=None)
    movie_collection = MovieCollection(page=1, total_pages=1, total_results=1, items=[movie])
    music = MusicSummary(id="track-1", name="Echoes", artists=["Nova"], source="track")
    music_collection = MusicCollection(total=1, limit=1, offset=0, items=[music])
    music_search = MusicSearchResults(query="ambient", total=1, limit=1, offset=0, items=[music])
    movie_search = MovieSearchResults(query="ambient", page=1, total_pages=1, total_results=1, items=[movie])

    class DummyTMDb:
        def __init__(self) -> None:
            self.popular_calls = 0

        def get_popular_movies(self, **_: Any) -> MovieCollection:
            self.popular_calls += 1
            return movie_collection

        def search_movies(self, **_: Any) -> MovieSearchResults:
            return movie_search

    class DummySpotify:
        def __init__(self) -> None:
            self.popular_calls = 0

        def get_popular_tracks(self, **_: Any) -> MusicCollection:
            self.popular_calls += 1
            return music_collection

        def search_tracks(self, **_: Any) -> MusicSearchResults:
            return music_search

    service = ContentDiscoveryService(tmdb_client=DummyTMDb(), spotify_client=DummySpotify(), popular_ttl_seconds=120)

    first_movies = service.popular_movies(limit=1)
    second_movies = service.popular_movies(limit=1)
    assert first_movies.items == second_movies.items
    assert service._tmdb.popular_calls == 1  # type: ignore[attr-defined]

    first_music = service.popular_music(limit=1)
    second_music = service.popular_music(limit=1)
    assert first_music.items == second_music.items
    assert service._spotify.popular_calls == 1  # type: ignore[attr-defined]

    search_movies = service.search_movies("ambient")
    search_music = service.search_music("ambient")
    assert search_movies.items[0].title == "Synthwave"
    assert search_music.items[0].name == "Echoes"
