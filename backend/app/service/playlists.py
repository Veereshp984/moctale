from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.core.database import get_database


PlaylistItemType = Literal["movie", "music"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def storage_dt(value: datetime) -> datetime:
    return _as_utc(value).replace(tzinfo=None)


class PlaylistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    is_public: bool = False
    allowed_users: list[str] = Field(default_factory=list)


class PlaylistUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    is_public: Optional[bool] = None
    allowed_users: Optional[list[str]] = None


class PlaylistItemIn(BaseModel):
    type: PlaylistItemType
    media_id: str = Field(min_length=1)
    metadata: dict[str, Any] | None = None
    position: Optional[int] = None


class PlaylistItemOut(BaseModel):
    id: str
    type: PlaylistItemType
    media_id: str
    metadata: dict[str, Any] | None = None
    position: int


class PlaylistOut(BaseModel):
    id: str
    owner_id: str
    name: str
    description: Optional[str] = None
    slug: str
    is_public: bool
    allowed_users: list[str]
    items: list[PlaylistItemOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


router = APIRouter(prefix="/playlists", tags=["playlists"])


async def _get_db() -> AsyncIOMotorDatabase:
    try:
        return get_database()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail="Database unavailable") from exc


async def _get_user_id(x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")) -> str:
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-User-Id header")
    return x_user_id


def _slugify(name: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "playlist"


async def _ensure_unique_slug(db: AsyncIOMotorDatabase, base_slug: str) -> str:
    slug = base_slug
    suffix = 1
    while await db["playlists"].find_one({"slug": slug}):
        suffix += 1
        slug = f"{base_slug}-{suffix}"
    return slug


async def _fetch_playlist(db: AsyncIOMotorDatabase, playlist_id: str) -> dict[str, Any]:
    try:
        oid = ObjectId(playlist_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Playlist not found") from exc
    doc = await db["playlists"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return doc


def _can_read(playlist: dict[str, Any], user_id: str | None) -> bool:
    if playlist.get("is_public"):
        return True
    if user_id and (playlist.get("owner_id") == user_id or user_id in playlist.get("allowed_users", [])):
        return True
    return False


def _can_modify(playlist: dict[str, Any], user_id: str) -> bool:
    return playlist.get("owner_id") == user_id or user_id in playlist.get("allowed_users", [])


async def _log_activity(
    db: AsyncIOMotorDatabase,
    *,
    user_id: str,
    playlist_id: str,
    action: str,
    details: dict[str, Any] | None = None,
) -> None:
    record = {
        "user_id": user_id,
        "playlist_id": playlist_id,
        "action": action,
        "details": details or {},
        "created_at": storage_dt(utcnow()),
    }
    await db["activities"].insert_one(record)


async def _serialize_playlist(db: AsyncIOMotorDatabase, playlist: dict[str, Any]) -> PlaylistOut:
    items_cursor = db["playlist_items"].find({"playlist_id": playlist["_id"]}).sort("position", 1)
    items: list[PlaylistItemOut] = []
    async for item in items_cursor:
        items.append(
            PlaylistItemOut(
                id=str(item["_id"]),
                type=item["type"],
                media_id=item["media_id"],
                metadata=item.get("metadata"),
                position=item["position"],
            )
        )
    return PlaylistOut(
        id=str(playlist["_id"]),
        owner_id=playlist["owner_id"],
        name=playlist["name"],
        description=playlist.get("description"),
        slug=playlist["slug"],
        is_public=playlist["is_public"],
        allowed_users=list(playlist.get("allowed_users", [])),
        items=items,
        created_at=_as_utc(playlist["created_at"]),
        updated_at=_as_utc(playlist["updated_at"]),
    )


@router.post("/", response_model=PlaylistOut, status_code=status.HTTP_201_CREATED)
async def create_playlist(
    payload: PlaylistCreate,
    db: AsyncIOMotorDatabase = Depends(_get_db),
    user_id: str = Depends(_get_user_id),
) -> PlaylistOut:
    base_slug = _slugify(payload.name)
    slug = await _ensure_unique_slug(db, base_slug)
    now = storage_dt(utcnow())
    doc = {
        "owner_id": user_id,
        "name": payload.name,
        "description": payload.description,
        "slug": slug,
        "is_public": payload.is_public,
        "allowed_users": list(dict.fromkeys(payload.allowed_users)),
        "created_at": now,
        "updated_at": now,
    }
    result = await db["playlists"].insert_one(doc)
    playlist_id = str(result.inserted_id)
    await _log_activity(db, user_id=user_id, playlist_id=playlist_id, action="playlist_created")
    stored = await db["playlists"].find_one({"_id": result.inserted_id})
    assert stored is not None
    return await _serialize_playlist(db, stored)


@router.get("/{playlist_id}", response_model=PlaylistOut)
async def get_playlist(
    playlist_id: str,
    db: AsyncIOMotorDatabase = Depends(_get_db),
    user_id: Optional[str] = Depends(_get_user_id),
) -> PlaylistOut:
    playlist = await _fetch_playlist(db, playlist_id)
    if not _can_read(playlist, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return await _serialize_playlist(db, playlist)


@router.get("/public/{identifier}", response_model=PlaylistOut)
async def get_public_playlist(identifier: str, db: AsyncIOMotorDatabase = Depends(_get_db)) -> PlaylistOut:
    doc = await db["playlists"].find_one({"slug": identifier, "is_public": True})
    if not doc:
        try:
            oid = ObjectId(identifier)
        except Exception as exc:
            raise HTTPException(status_code=404, detail="Playlist not found") from exc
        doc = await db["playlists"].find_one({"_id": oid, "is_public": True})
    if not doc:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return await _serialize_playlist(db, doc)


@router.patch("/{playlist_id}", response_model=PlaylistOut)
async def update_playlist(
    playlist_id: str,
    payload: PlaylistUpdate,
    db: AsyncIOMotorDatabase = Depends(_get_db),
    user_id: str = Depends(_get_user_id),
) -> PlaylistOut:
    playlist = await _fetch_playlist(db, playlist_id)
    if playlist["owner_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can update playlist")

    update: dict[str, Any] = {}
    if payload.name is not None and payload.name != playlist["name"]:
        update["name"] = payload.name
        base_slug = _slugify(payload.name)
        update["slug"] = await _ensure_unique_slug(db, base_slug)
    if payload.description is not None:
        update["description"] = payload.description
    if payload.is_public is not None:
        update["is_public"] = payload.is_public
    if payload.allowed_users is not None:
        update["allowed_users"] = list(dict.fromkeys(payload.allowed_users))
    if not update:
        return await _serialize_playlist(db, playlist)

    update["updated_at"] = storage_dt(utcnow())
    await db["playlists"].update_one({"_id": playlist["_id"]}, {"$set": update})
    await _log_activity(db, user_id=user_id, playlist_id=playlist_id, action="playlist_updated", details=update)
    refreshed = await _fetch_playlist(db, playlist_id)
    return await _serialize_playlist(db, refreshed)


@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlist(
    playlist_id: str,
    db: AsyncIOMotorDatabase = Depends(_get_db),
    user_id: str = Depends(_get_user_id),
) -> None:
    playlist = await _fetch_playlist(db, playlist_id)
    if playlist["owner_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can delete playlist")

    await db["playlist_items"].delete_many({"playlist_id": playlist["_id"]})
    await db["playlists"].delete_one({"_id": playlist["_id"]})
    await _log_activity(db, user_id=user_id, playlist_id=playlist_id, action="playlist_deleted")


@router.post("/{playlist_id}/items", response_model=PlaylistOut)
async def add_item(
    playlist_id: str,
    payload: PlaylistItemIn,
    db: AsyncIOMotorDatabase = Depends(_get_db),
    user_id: str = Depends(_get_user_id),
) -> PlaylistOut:
    playlist = await _fetch_playlist(db, playlist_id)
    if not _can_modify(playlist, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to modify playlist")

    # determine insert position
    if payload.position is None:
        last = await db["playlist_items"].find({"playlist_id": playlist["_id"]}).sort("position", -1).to_list(1)
        position = (last[0]["position"] + 1) if last else 0
    else:
        # shift positions >= payload.position by +1
        position = max(0, int(payload.position))
        await db["playlist_items"].update_many(
            {"playlist_id": playlist["_id"], "position": {"$gte": position}}, {"$inc": {"position": 1}}
        )

    item_doc = {
        "playlist_id": playlist["_id"],
        "type": payload.type,
        "media_id": payload.media_id,
        "metadata": payload.metadata or {},
        "position": position,
        "created_at": storage_dt(utcnow()),
    }
    result = await db["playlist_items"].insert_one(item_doc)
    await _log_activity(
        db,
        user_id=user_id,
        playlist_id=playlist_id,
        action="item_added",
        details={"item_id": str(result.inserted_id), "type": payload.type, "media_id": payload.media_id},
    )
    refreshed = await _fetch_playlist(db, playlist_id)
    return await _serialize_playlist(db, refreshed)


@router.delete("/{playlist_id}/items/{item_id}", response_model=PlaylistOut)
async def remove_item(
    playlist_id: str,
    item_id: str,
    db: AsyncIOMotorDatabase = Depends(_get_db),
    user_id: str = Depends(_get_user_id),
) -> PlaylistOut:
    playlist = await _fetch_playlist(db, playlist_id)
    if not _can_modify(playlist, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to modify playlist")

    try:
        oid = ObjectId(item_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Item not found") from exc

    item = await db["playlist_items"].find_one({"_id": oid, "playlist_id": playlist["_id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    removed_position = item["position"]
    await db["playlist_items"].delete_one({"_id": oid})
    # shift positions > removed_position by -1
    await db["playlist_items"].update_many(
        {"playlist_id": playlist["_id"], "position": {"$gt": removed_position}}, {"$inc": {"position": -1}}
    )
    await _log_activity(
        db,
        user_id=user_id,
        playlist_id=playlist_id,
        action="item_removed",
        details={"item_id": item_id},
    )
    refreshed = await _fetch_playlist(db, playlist_id)
    return await _serialize_playlist(db, refreshed)


class ReorderPayload(BaseModel):
    item_ids: list[str]


@router.post("/{playlist_id}/reorder", response_model=PlaylistOut)
async def reorder_items(
    playlist_id: str,
    payload: ReorderPayload,
    db: AsyncIOMotorDatabase = Depends(_get_db),
    user_id: str = Depends(_get_user_id),
) -> PlaylistOut:
    playlist = await _fetch_playlist(db, playlist_id)
    if not _can_modify(playlist, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to modify playlist")

    items = await db["playlist_items"].find({"playlist_id": playlist["_id"]}).to_list(length=None)
    existing_ids = {str(doc["_id"]) for doc in items}
    new_order = payload.item_ids
    if set(new_order) != existing_ids:
        raise HTTPException(status_code=400, detail="New order must include all items exactly once")

    # map id -> new position
    position_map = {item_id: idx for idx, item_id in enumerate(new_order)}
    for doc in items:
        new_pos = position_map[str(doc["_id"])]
        if doc["position"] != new_pos:
            await db["playlist_items"].update_one({"_id": doc["_id"]}, {"$set": {"position": new_pos}})

    await _log_activity(db, user_id=user_id, playlist_id=playlist_id, action="items_reordered")
    refreshed = await _fetch_playlist(db, playlist_id)
    return await _serialize_playlist(db, refreshed)


class ShareInvitePayload(BaseModel):
    user_id: str


@router.post("/{playlist_id}/share/invite", response_model=PlaylistOut)
async def invite_user(
    playlist_id: str,
    payload: ShareInvitePayload,
    db: AsyncIOMotorDatabase = Depends(_get_db),
    user_id: str = Depends(_get_user_id),
) -> PlaylistOut:
    playlist = await _fetch_playlist(db, playlist_id)
    if playlist["owner_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can modify sharing")

    allowed = list(dict.fromkeys(playlist.get("allowed_users", []) + [payload.user_id]))
    await db["playlists"].update_one(
        {"_id": playlist["_id"]}, {"$set": {"allowed_users": allowed, "updated_at": storage_dt(utcnow())}}
    )
    await _log_activity(
        db,
        user_id=user_id,
        playlist_id=playlist_id,
        action="share_invited",
        details={"invited_user_id": payload.user_id},
    )
    refreshed = await _fetch_playlist(db, playlist_id)
    return await _serialize_playlist(db, refreshed)


@router.delete("/{playlist_id}/share/allowed/{shared_user_id}", response_model=PlaylistOut)
async def revoke_user(
    playlist_id: str,
    shared_user_id: str,
    db: AsyncIOMotorDatabase = Depends(_get_db),
    user_id: str = Depends(_get_user_id),
) -> PlaylistOut:
    playlist = await _fetch_playlist(db, playlist_id)
    if playlist["owner_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can modify sharing")

    allowed = [uid for uid in playlist.get("allowed_users", []) if uid != shared_user_id]
    await db["playlists"].update_one(
        {"_id": playlist["_id"]}, {"$set": {"allowed_users": allowed, "updated_at": storage_dt(utcnow())}}
    )
    await _log_activity(
        db,
        user_id=user_id,
        playlist_id=playlist_id,
        action="share_revoked",
        details={"revoked_user_id": shared_user_id},
    )
    refreshed = await _fetch_playlist(db, playlist_id)
    return await _serialize_playlist(db, refreshed)


def attach_playlist_routes(app: FastAPI) -> None:
    app.include_router(router)

    @app.on_event("startup")
    async def _create_indexes() -> None:  # pragma: no cover - trivial index creation
        db = get_database()
        await db["playlists"].create_index("slug", unique=True)
        await db["playlist_items"].create_index([("playlist_id", 1), ("position", 1)], unique=True)
        await db["playlist_items"].create_index("playlist_id")
