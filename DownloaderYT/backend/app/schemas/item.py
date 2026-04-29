from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ItemRetryResponse(BaseModel):
    message: str
    item_id: int
    status: str
    updated_at: datetime

