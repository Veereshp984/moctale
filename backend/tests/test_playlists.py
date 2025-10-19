from __future__ import annotations

from importlib import reload
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

from app.core import database


@pytest.fixture()
def playlist_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    # configure in-memory Mongo and reset state
    monkeypatch.setenv("MONGODB_URL", "mongodb://localhost/test-playlists")
    monkeypatch.setenv("MONGODB_DB_NAME", "test-playlists-db")
    monkeypatch.setattr(database, "AsyncIOMotorClient", AsyncMongoMockClient)

    database.mongo_manager.reset()

    from app.service import api

    reload(api)
    with TestClient(api.app) as client:
        yield client

    database.mongo_manager.reset()
    api._service_factory.cache_clear()


def _headers(user_id: str) -> dict[str, str]:
    return {"X-User-Id": user_id}


def test_create_update_and_delete_playlist_with_mixed_items(playlist_client: TestClient) -> None:
    # Create a private playlist for user u1
    create_resp = playlist_client.post(
        "/playlists/",
        json={
            "name": "My Mix",
            "description": "Chill vibes",
            "is_public": False,
        },
        headers=_headers("u1"),
    )
    assert create_resp.status_code == 201
    playlist = create_resp.json()
    assert playlist["name"] == "My Mix"
    assert playlist["is_public"] is False
    assert playlist["items"] == []
    pid = playlist["id"]

    # Add a movie and a music track
    add_movie = playlist_client.post(
        f"/playlists/{pid}/items",
        json={"type": "movie", "media_id": "movie_42", "metadata": {"title": "The Film"}},
        headers=_headers("u1"),
    )
    assert add_movie.status_code == 200
    playlist = add_movie.json()
    assert len(playlist["items"]) == 1
    assert playlist["items"][0]["type"] == "movie"

    add_music = playlist_client.post(
        f"/playlists/{pid}/items",
        json={"type": "music", "media_id": "track_9", "metadata": {"title": "A Song"}},
        headers=_headers("u1"),
    )
    assert add_music.status_code == 200
    playlist = add_music.json()
    assert [it["type"] for it in playlist["items"]] == ["movie", "music"]

    # Reorder items
    item_ids = [it["id"] for it in playlist["items"]]
    reorder = playlist_client.post(
        f"/playlists/{pid}/reorder",
        json={"item_ids": list(reversed(item_ids))},
        headers=_headers("u1"),
    )
    assert reorder.status_code == 200
    playlist = reorder.json()
    assert [it["type"] for it in playlist["items"]] == ["music", "movie"]

    # Remove one item
    remove = playlist_client.delete(
        f"/playlists/{pid}/items/{playlist['items'][0]['id']}",
        headers=_headers("u1"),
    )
    assert remove.status_code == 200
    playlist = remove.json()
    assert [it["type"] for it in playlist["items"]] == ["movie"]

    # Update metadata and make public
    update = playlist_client.patch(
        f"/playlists/{pid}",
        json={"name": "My New Mix", "description": "Updated", "is_public": True},
        headers=_headers("u1"),
    )
    assert update.status_code == 200
    playlist = update.json()
    assert playlist["name"] == "My New Mix"
    assert playlist["is_public"] is True

    # Delete playlist
    delete = playlist_client.delete(f"/playlists/{pid}", headers=_headers("u1"))
    assert delete.status_code == 204

    # Fetching should now 404
    not_found = playlist_client.get(f"/playlists/{pid}", headers=_headers("u1"))
    assert not_found.status_code == 404


def test_public_and_private_access_enforced(playlist_client: TestClient) -> None:
    # u1 creates a private playlist
    create_resp = playlist_client.post(
        "/playlists/",
        json={"name": "Secret Mix", "is_public": False},
        headers=_headers("u1"),
    )
    pid = create_resp.json()["id"]
    slug = create_resp.json()["slug"]

    # u2 cannot access private playlist
    denied = playlist_client.get(f"/playlists/{pid}", headers=_headers("u2"))
    assert denied.status_code == 403

    # Public endpoint must not reveal private playlists
    not_found = playlist_client.get(f"/playlists/public/{slug}")
    assert not_found.status_code == 404

    # Make it public
    update = playlist_client.patch(f"/playlists/{pid}", json={"is_public": True}, headers=_headers("u1"))
    assert update.status_code == 200

    # Now anyone can fetch by id or slug
    public_by_id = playlist_client.get(f"/playlists/public/{pid}")
    assert public_by_id.status_code == 200
    public_by_slug = playlist_client.get(f"/playlists/public/{slug}")
    assert public_by_slug.status_code == 200


def test_sharing_invite_and_revoke_permissions(playlist_client: TestClient) -> None:
    # u1 creates a private playlist and invites u2
    resp = playlist_client.post(
        "/playlists/",
        json={"name": "Collab", "is_public": False},
        headers=_headers("u1"),
    )
    pid = resp.json()["id"]

    invite = playlist_client.post(
        f"/playlists/{pid}/share/invite", json={"user_id": "u2"}, headers=_headers("u1")
    )
    assert invite.status_code == 200
    assert "u2" in invite.json()["allowed_users"]

    # u2 can view and modify
    view = playlist_client.get(f"/playlists/{pid}", headers=_headers("u2"))
    assert view.status_code == 200

    add = playlist_client.post(
        f"/playlists/{pid}/items",
        json={"type": "music", "media_id": "x"},
        headers=_headers("u2"),
    )
    assert add.status_code == 200
    assert len(add.json()["items"]) == 1

    # Owner can revoke
    revoke = playlist_client.delete(f"/playlists/{pid}/share/allowed/u2", headers=_headers("u1"))
    assert revoke.status_code == 200
    assert "u2" not in revoke.json()["allowed_users"]

    # u2 loses access
    denied = playlist_client.get(f"/playlists/{pid}", headers=_headers("u2"))
    assert denied.status_code == 403
