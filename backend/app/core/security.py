from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(password, hashed_password)
    except ValueError:
        return False


def create_access_token(
    subject: str,
    *,
    settings: Settings | None = None,
    expires_delta: timedelta | None = None,
) -> tuple[str, datetime]:
    if settings is None:
        settings = get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: Dict[str, Any] = {"sub": subject, "exp": expire}
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expire


def decode_access_token(token: str, *, settings: Settings | None = None) -> Dict[str, Any]:
    if settings is None:
        settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


class TokenDecodeError(Exception):
    pass


def parse_token(token: str, *, settings: Settings | None = None) -> Dict[str, Any]:
    try:
        return decode_access_token(token, settings=settings)
    except JWTError as exc:  # pragma: no cover - the exception mapping is simple
        raise TokenDecodeError("Invalid token") from exc
