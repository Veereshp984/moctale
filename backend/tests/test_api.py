"""Smoke tests for the FastAPI recommendation endpoint."""
from __future__ import annotations

from importlib import reload
from pathlib import Path
from typing import Any, Iterator

import pytest
from fastapi.testclient import TestClient

from app.data import pipeline
from app.model import train
from app.service import discovery


class DummyDiscoveryService:
    def __init__(self) -> None:
        self.popular_movies_calls: list[dict[str, Any]] = []
        self.search_movies_calls: list[dict[str, Any]] = []
        self.popular_music_calls: list[dict[str, Any]] = []
        self.search_music_calls: list[dict[str, Any]] = []
        self.popular_movies_response: discovery.MovieCollection | None = None
        self.search_movies_response: discovery.MovieSearchResults | None = None
        self.popular_music_response: discovery.MusicCollection | None = None
        self.search_music_response: discovery.MusicSearchResults | None = None

    def popular_movies(self, **kwargs: Any) -> discovery.MovieCollection:
        self.popular_movies_calls.append(kwargs)
        if self.popular_movies_response is None:
            raise AssertionError("popular_movies_response not configured")
        return self.popular_movies_response

    def search_movies(self, **kwargs: Any) -> discovery.MovieSearchResults:
        self.search_movies_calls.append(kwargs)
        if self.search_movies_response is None:
            raise AssertionError("search_movies_response not configured")
        return self.search_movies_response

    def popular_music(self, **kwargs: Any) -> discovery.MusicCollection:
        self.popular_music_calls.append(kwargs)
        if self.popular_music_response is None:
            raise AssertionError("popular_music_response not configured")
        return self.popular_music_response

    def search_music(self, **kwargs: Any) -> discovery.MusicSearchResults:
        self.search_music_calls.append(kwargs)
        if self.search_music_response is None:
            raise AssertionError("search_music_response not configured")
        return self.search_music_response


@pytest.fixture(scope="session")
def trained_model_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    tmp_dir = tmp_path_factory.mktemp("model")
    raw_interactions = [
        {"user_id": "alice", "item_id": "track_1", "event_type": "like"},
        {"user_id": "alice", "item_id": "track_2", "event_type": "playlist_add"},
        {"user_id": "bob", "item_id": "track_2", "event_type": "like"},
        {"user_id": "bob", "item_id": "track_3", "event_type": "playlist_add"},
        {"user_id": "carol", "item_id": "track_3", "event_type": "like"},
        {"user_id": "dave", "item_id": "track_4", "event_type": "playlist_add"},
    ]
    interactions = pipeline.normalize_interactions(raw_interactions)
    train.train_model_from_interactions(
        interactions,
        model_dir=tmp_dir,
        embedding_dim=4,
        epochs=3,
        batch_size=8,
        learning_rate=0.005,
        num_negatives=2,
        seed=7,
    )
    return tmp_dir


@pytest.fixture()
def api_client(monkeypatch: pytest.MonkeyPatch, trained_model_dir: Path) -> Iterator[TestClient]:
    monkeypatch.setenv("RECOMMENDER_MODEL_DIR", str(trained_model_dir))
    from app.service import api

    reload(api)
    client = TestClient(api.app)
    try:
        yield client
    finally:
        # clear cached service between tests
        api._service_factory.cache_clear()
        if hasattr(api, "_discovery_service_factory"):
            api._discovery_service_factory.cache_clear()


def test_recommendations_endpoint_returns_personalised_results(api_client: TestClient) -> None:
    response = api_client.get("/recommendations/alice", params={"limit": 3})
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "alice"
    assert len(payload["recommendations"]) == 3
    assert payload["fallback_used"] is False


def test_unknown_user_triggers_popularity_fallback(api_client: TestClient) -> None:
    response = api_client.get("/recommendations/unknown", params={"limit": 2})
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "unknown"
    assert len(payload["recommendations"]) == 2
    assert payload["fallback_used"] is True


def test_popular_movies_endpoint_returns_payload(
    api_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.service import api as api_module

    service = DummyDiscoveryService()
    service.popular_movies_response = discovery.MovieCollection(
        page=1,
        total_pages=1,
        total_results=1,
        items=[
            discovery.MovieSummary(
                id="m-1",
                title="Synthwave Dreams",
                overview="Neon-lit journeys through retro futures.",
                poster_url="https://example.com/poster.jpg",
            )
        ],
    )
    monkeypatch.setattr(api_module, "get_discovery_service", lambda: service)

    response = api_client.get("/discovery/movies/popular", params={"limit": 1, "region": "us"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["title"] == "Synthwave Dreams"
    assert service.popular_movies_calls[0]["region"] == "US"
    assert service.popular_movies_calls[0]["limit"] == 1


def test_search_movies_endpoint_forwards_parameters(
    api_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.service import api as api_module

    service = DummyDiscoveryService()
    service.search_movies_response = discovery.MovieSearchResults(
        query="tron",
        page=2,
        total_pages=4,
        total_results=40,
        items=[
            discovery.MovieSummary(
                id="m-2",
                title="Tron Legacy",
                overview="A journey through the grid.",
                language="fr",
            )
        ],
    )
    monkeypatch.setattr(api_module, "get_discovery_service", lambda: service)

    response = api_client.get(
        "/discovery/movies/search",
        params={"query": "tron", "page": 2, "language": "fr"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "tron"
    assert payload["page"] == 2
    assert service.search_movies_calls[0]["language"] == "fr"
    assert service.search_movies_calls[0]["page"] == 2


def test_popular_music_endpoint_returns_payload(
    api_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.service import api as api_module

    service = DummyDiscoveryService()
    service.popular_music_response = discovery.MusicCollection(
        total=1,
        limit=1,
        offset=0,
        items=[
            discovery.MusicSummary(
                id="track-1",
                name="Glitched Horizons",
                artists=["Nova"],
                album="Glitch Season",
                external_url="https://example.com/track",
                source="album",
            )
        ],
    )
    monkeypatch.setattr(api_module, "get_discovery_service", lambda: service)

    response = api_client.get("/discovery/music/popular", params={"market": "gb", "limit": 1})

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["name"] == "Glitched Horizons"
    assert service.popular_music_calls[0]["market"] == "GB"


def test_search_music_endpoint_returns_payload(
    api_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.service import api as api_module

    service = DummyDiscoveryService()
    service.search_music_response = discovery.MusicSearchResults(
        query="ambient",
        total=1,
        limit=5,
        offset=0,
        items=[
            discovery.MusicSummary(
                id="track-2",
                name="Aurora",
                artists=["Flux"],
                album="Nightfall",
                preview_url="https://example.com/preview",
                source="track",
            )
        ],
    )
    monkeypatch.setattr(api_module, "get_discovery_service", lambda: service)

    response = api_client.get(
        "/discovery/music/search",
        params={"query": "ambient", "limit": 5, "market": "us"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["name"] == "Aurora"
    assert payload["query"] == "ambient"
    assert service.search_music_calls[0]["limit"] == 5


def test_popular_music_endpoint_handles_rate_limit(
    api_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.service import api as api_module

    class FailingDiscoveryService:
        def popular_music(self, **_: Any) -> discovery.MusicCollection:
            raise discovery.RateLimitError("Limit", provider="spotify", retry_after=5)

    monkeypatch.setattr(api_module, "get_discovery_service", lambda: FailingDiscoveryService())

    response = api_client.get("/discovery/music/popular")

    assert response.status_code == 429
    assert response.headers.get("Retry-After") == "5"
