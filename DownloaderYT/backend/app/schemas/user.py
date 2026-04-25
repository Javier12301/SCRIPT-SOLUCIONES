from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class UserPublic(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

