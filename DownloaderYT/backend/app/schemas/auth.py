from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserPublic


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    message: str
    user: UserPublic
    expires_at: datetime


class MeResponse(BaseModel):
    user: UserPublic


class LogoutResponse(BaseModel):
    message: str

