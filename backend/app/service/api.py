"""FastAPI service exposing recommendation and authentication endpoints."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from bson import ObjectId
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.database import close_database, get_database, init_database
from app.core.security import TokenDecodeError, create_access_token, hash_password, parse_token, verify_password
from app.model.recommender import RecommendationService
from app.schemas.auth import AuthTokenRecord, TokenResponse, UserCreate, UserLogin, UserPreferences, UserPublic
from app.service.discovery_api import discovery_router

BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_ROOT = BASE_DIR.parent
DEFAULT_MODEL_DIR = BACKEND_ROOT / "models" / "latest"

app = FastAPI(title="Soundwave Recommendation Service", version="1.1.0")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
auth_router = APIRouter(prefix="/auth", tags=["auth"])


def _get_settings() -> Settings:
    return get_settings()


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _get_db() -> AsyncIOMotorDatabase:
    try:
        return get_database()
    except RuntimeError as exc:  # pragma: no cover - FastAPI startup ensures init
        raise HTTPException(status_code=500, detail="Database unavailable") from exc


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _storage_datetime(value: datetime) -> datetime:
    return _as_utc(value).replace(tzinfo=None)


async def _fetch_preferences(db: AsyncIOMotorDatabase, user_id: str) -> UserPreferences:
    document = await db["user_preferences"].find_one({"user_id": user_id})
    if document and document.get("preferences"):
        return UserPreferences(**document["preferences"])
    return UserPreferences()


async def _store_token(db: AsyncIOMotorDatabase, token: str, user_id: str, expires_at: datetime) -> None:
    record = AuthTokenRecord(
        token=token,
        user_id=user_id,
        expires_at=_storage_datetime(expires_at),
        created_at=_storage_datetime(utcnow()),
    )
    await db["auth_tokens"].insert_one(record.model_dump())


@app.on_event("startup")
async def on_startup() -> None:
    init_database()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    close_database()
    _service_factory.cache_clear()


class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: list[str]
    fallback_used: bool


@lru_cache()
def _service_factory(model_dir: str) -> RecommendationService:
    return RecommendationService(model_dir)


def get_service() -> RecommendationService:
    model_dir = Path(os.getenv("RECOMMENDER_MODEL_DIR", str(DEFAULT_MODEL_DIR))).resolve()
    try:
        return _service_factory(str(model_dir))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Model artifacts unavailable") from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/recommendations/{user_id}", response_model=RecommendationResponse)
def get_recommendations(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=100, description="Number of recommendations to return"),
    service: RecommendationService = Depends(get_service),
) -> RecommendationResponse:
    try:
        recommendations, fallback_used = service.recommend_for_user(user_id, limit)
    except Exception as exc:  # noqa: BLE001 - surface predictable error payload
        raise HTTPException(status_code=500, detail="Recommendation inference failed") from exc
    if not recommendations:
        raise HTTPException(status_code=404, detail="No recommendations available")
    return RecommendationResponse(user_id=user_id, recommendations=recommendations, fallback_used=fallback_used)


@auth_router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup_user(
    payload: UserCreate,
    db: AsyncIOMotorDatabase = Depends(_get_db),
    settings: Settings = Depends(_get_settings),
) -> TokenResponse:
    email = payload.email.lower()
    existing = await db["users"].find_one({"email": email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    now = utcnow()
    stored_now = _storage_datetime(now)
    hashed_password = hash_password(payload.password)
    user_doc = {"email": email, "hashed_password": hashed_password, "created_at": stored_now}
    result = await db["users"].insert_one(user_doc)
    user_id = str(result.inserted_id)

    preferences = payload.preferences or UserPreferences()
    await db["user_preferences"].insert_one(
        {
            "user_id": user_id,
            "preferences": preferences.model_dump(),
            "created_at": stored_now,
            "updated_at": stored_now,
        }
    )

    token, expires_at = create_access_token(user_id, settings=settings)
    await _store_token(db, token, user_id, expires_at)

    user_public = UserPublic(id=user_id, email=email, preferences=preferences)
    return TokenResponse(access_token=token, user=user_public)


@auth_router.post("/login", response_model=TokenResponse)
async def login_user(
    payload: UserLogin,
    db: AsyncIOMotorDatabase = Depends(_get_db),
    settings: Settings = Depends(_get_settings),
) -> TokenResponse:
    email = payload.email.lower()
    user_doc = await db["users"].find_one({"email": email})
    if user_doc is None or not verify_password(payload.password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = str(user_doc["_id"])
    token, expires_at = create_access_token(user_id, settings=settings)
    await _store_token(db, token, user_id, expires_at)

    preferences = await _fetch_preferences(db, user_id)
    user_public = UserPublic(id=user_id, email=user_doc["email"], preferences=preferences)
    return TokenResponse(access_token=token, user=user_public)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(_get_db),
    settings: Settings = Depends(_get_settings),
) -> UserPublic:
    auth_error = _credentials_exception()
    try:
        payload = parse_token(token, settings=settings)
    except TokenDecodeError as exc:  # pragma: no cover - simple error mapping
        raise auth_error from exc

    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise auth_error

    token_doc = await db["auth_tokens"].find_one({"token": token})
    if not token_doc:
        raise auth_error

    expires_at = token_doc.get("expires_at")
    if isinstance(expires_at, datetime) and _as_utc(expires_at) < utcnow():
        raise auth_error

    try:
        object_id = ObjectId(user_id)
    except Exception as exc:  # pragma: no cover - invalid ObjectId path is rare
        raise auth_error from exc

    user_doc = await db["users"].find_one({"_id": object_id})
    if not user_doc:
        raise auth_error

    preferences = await _fetch_preferences(db, str(user_doc["_id"]))
    return UserPublic(id=str(user_doc["_id"]), email=user_doc["email"], preferences=preferences)


@auth_router.get("/me", response_model=UserPublic)
async def read_current_user(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    return current_user


app.include_router(auth_router)
app.include_router(discovery_router)
