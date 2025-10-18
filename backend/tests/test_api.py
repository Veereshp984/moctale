"""Smoke tests for the FastAPI recommendation endpoint."""
from __future__ import annotations

from importlib import reload
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from app.data import pipeline
from app.model import train


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
