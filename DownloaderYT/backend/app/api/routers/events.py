from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/events")
def events_placeholder() -> dict[str, str]:
    return {"message": "Fase 4: SSE pendiente"}
