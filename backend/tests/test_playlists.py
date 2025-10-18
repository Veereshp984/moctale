"""Integration tests for playlist and sharing workflows."""
from __future__ import annotations

from importlib import reload
from typing import Iterator

import mongomock
from mongomock.database import Database as MockDatabase
import pytest
from fastapi.testclient import TestClient

from app.service.db import get_database


@pytest.fixture()
def mongo_database() -> MockDatabase:
    client = mongomock.MongoClient()
    return client["soundwave_test"]


@pytest.fixture()
def api_client(mongo_database: MockDatabase) -> Iterator[TestClient]:
    from app.service import api

    reload(api)
    api.app.dependency_overrides[get_database] = lambda: mongo_database
    client = TestClient(api.app)
    try:
        yield client
    finally:
        client.close()
        api.app.dependency_overrides.pop(get_database, None)
        api._service_factory.cache_clear()


def test_playlist_crud_and_sharing_flow(api_client: TestClient, mongo_database: MockDatabase) -> None:
    create_payload = {
        "user_id": "creator-1",
        "name": "Weekend Vibes",
        "description": "Mix of movies and music for the weekend",
        "is_public": False,
        "invited_users": ["alice", "bob", "alice"],
    }
    response = api_client.post("/playlists", json=create_payload)
    assert response.status_code == 201
    playlist = response.json()
    playlist_id = playlist["id"]
    assert playlist["name"] == "Weekend Vibes"
    assert playlist["invited_users"] == ["alice", "bob"]
    assert playlist["items"] == []

    update_payload = {"name": "Weekend Chill", "description": "Updated description"}
    response = api_client.patch(f"/playlists/{playlist_id}", json=update_payload)
    assert response.status_code == 200
    playlist = response.json()
    assert playlist["name"] == "Weekend Chill"
    assert playlist["description"] == "Updated description"

    add_items_payload = {
        "items": [
            {"source_id": "movie_42", "media_type": "movie", "title": "The Answer"},
            {"source_id": "track_99", "media_type": "music", "title": "Skyline"},
        ]
    }
    response = api_client.post(f"/playlists/{playlist_id}/items", json=add_items_payload)
    assert response.status_code == 200
    playlist = response.json()
    assert len(playlist["items"]) == 2
    assert playlist["items"][0]["media_type"] == "movie"
    assert playlist["items"][1]["media_type"] == "music"

    first_item_id = playlist["items"][0]["item_id"]
    second_item_id = playlist["items"][1]["item_id"]

    reorder_payload = {"order": [second_item_id, first_item_id]}
    response = api_client.put(f"/playlists/{playlist_id}/items/reorder", json=reorder_payload)
    assert response.status_code == 200
    playlist = response.json()
    reordered_items = playlist["items"]
    assert reordered_items[0]["item_id"] == second_item_id
    assert reordered_items[0]["position"] == 0
    assert reordered_items[1]["position"] == 1

    response = api_client.delete(f"/playlists/{playlist_id}/items/{first_item_id}")
    assert response.status_code == 200
    playlist = response.json()
    assert len(playlist["items"]) == 1
    assert playlist["items"][0]["position"] == 0

    share_payload = {
        "is_public": True,
        "invited_users": ["charlie", "bob", "charlie"],
        "generate_invite": True,
    }
    response = api_client.put(f"/playlists/{playlist_id}/share", json=share_payload)
    assert response.status_code == 200
    share_details = response.json()
    assert share_details["is_public"] is True
    assert share_details["invited_users"] == ["charlie", "bob"]
    assert share_details["share_token"]
    share_token = share_details["share_token"]

    response = api_client.get("/playlists/public")
    assert response.status_code == 200
    public_playlists = response.json()
    assert len(public_playlists) == 1
    assert public_playlists[0]["id"] == playlist_id

    response = api_client.get(f"/share/{share_token}")
    assert response.status_code == 200
    shared_playlist = response.json()
    assert shared_playlist["id"] == playlist_id

    response = api_client.delete(f"/playlists/{playlist_id}")
    assert response.status_code == 204

    response = api_client.get(f"/playlists/{playlist_id}")
    assert response.status_code == 404

    activity_events = list(mongo_database["playlist_activity"].find({"playlist_id": playlist_id}))
    event_types = {event["event_type"] for event in activity_events}
    expected_events = {
        "playlist_created",
        "playlist_updated",
        "playlist_items_added",
        "playlist_items_reordered",
        "playlist_item_removed",
        "playlist_share_updated",
        "playlist_deleted",
    }
    assert expected_events.issubset(event_types)


def test_share_update_with_conflicting_flags(api_client: TestClient) -> None:
    response = api_client.post(
        "/playlists",
        json={
            "user_id": "creator-2",
            "name": "Conflicting Share",
            "description": None,
            "is_public": False,
            "invited_users": [],
        },
    )
    assert response.status_code == 201
    playlist_id = response.json()["id"]

    share_payload = {"generate_invite": True, "revoke_token": True}
    response = api_client.put(f"/playlists/{playlist_id}/share", json=share_payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot generate and revoke an invite in the same request"
