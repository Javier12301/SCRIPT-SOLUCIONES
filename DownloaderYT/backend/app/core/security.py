from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def generate_session_token() -> str:
    return secrets.token_urlsafe(48)


def hash_session_token(token: str, secret_key: str) -> str:
    payload = f"{secret_key}:{token}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_session_expiry(ttl_hours: int) -> datetime:
    return datetime.utcnow() + timedelta(hours=ttl_hours)

