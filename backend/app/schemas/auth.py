from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserPreferences(BaseModel):
    genres: list[str] = Field(default_factory=list)
    artists: list[str] = Field(default_factory=list)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    preferences: Optional[UserPreferences] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    id: str
    email: EmailStr
    hashed_password: str
    created_at: datetime


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    preferences: Optional[UserPreferences] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserPublic] = None


class AuthTokenRecord(BaseModel):
    token: str
    user_id: str
    expires_at: datetime
    created_at: datetime
