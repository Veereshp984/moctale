from __future__ import annotations

from importlib import reload
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

from app.core import database


@pytest.fixture()
def auth_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("MONGODB_URL", "mongodb://localhost/test-auth")
    monkeypatch.setenv("MONGODB_DB_NAME", "test-auth-db")
    monkeypatch.setenv("JWT_SECRET_KEY", "unit-test-secret")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    monkeypatch.setattr(database, "AsyncIOMotorClient", AsyncMongoMockClient)

    database.mongo_manager.reset()

    from app.service import api

    reload(api)
    with TestClient(api.app) as client:
        yield client

    database.mongo_manager.reset()
    api._service_factory.cache_clear()


def test_signup_creates_user_and_persists_preferences(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/auth/signup",
        json={
            "email": "listener@example.com",
            "password": "Sup3rSecr3t!",
            "preferences": {
                "genres": ["rock", "ambient"],
                "artists": ["artist-a"],
            },
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["user"]["email"] == "listener@example.com"
    assert payload["user"]["preferences"]["genres"] == ["rock", "ambient"]
    assert payload["access_token"]

    me_response = auth_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {payload['access_token']}"},
    )
    assert me_response.status_code == 200
    me_payload = me_response.json()
    assert me_payload["email"] == "listener@example.com"
    assert me_payload["preferences"]["artists"] == ["artist-a"]


def test_duplicate_signup_returns_conflict(auth_client: TestClient) -> None:
    first = auth_client.post(
        "/auth/signup",
        json={
            "email": "dupe@example.com",
            "password": "Sup3rSecr3t!",
        },
    )
    assert first.status_code == 201

    duplicate = auth_client.post(
        "/auth/signup",
        json={
            "email": "dupe@example.com",
            "password": "Sup3rSecr3t!",
        },
    )
    assert duplicate.status_code == 409


def test_login_returns_new_access_token(auth_client: TestClient) -> None:
    signup = auth_client.post(
        "/auth/signup",
        json={
            "email": "signin@example.com",
            "password": "Sup3rSecr3t!",
        },
    )
    assert signup.status_code == 201

    login = auth_client.post(
        "/auth/login",
        json={
            "email": "signin@example.com",
            "password": "Sup3rSecr3t!",
        },
    )
    assert login.status_code == 200
    payload = login.json()
    assert payload["access_token"]
    assert payload["user"]["email"] == "signin@example.com"


def test_login_rejects_invalid_password(auth_client: TestClient) -> None:
    auth_client.post(
        "/auth/signup",
        json={
            "email": "invalid@example.com",
            "password": "Sup3rSecr3t!",
        },
    )

    response = auth_client.post(
        "/auth/login",
        json={
            "email": "invalid@example.com",
            "password": "wrong",
        },
    )
    assert response.status_code == 401


def test_protected_route_requires_authorisation(auth_client: TestClient) -> None:
    response = auth_client.get("/auth/me")
    assert response.status_code == 401
