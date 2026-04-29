from __future__ import annotations

from pydantic import BaseModel


class SSEEvent(BaseModel):
    type: str

