from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.post("/{item_id}/retry")
def retry_item_placeholder(item_id: int) -> dict[str, str | int]:
    return {"message": "Fase 4: retry item pendiente", "item_id": item_id}


@router.get("/{item_id}/download")
def download_item_placeholder(item_id: int) -> dict[str, str | int]:
    return {"message": "Fase 4: download item pendiente", "item_id": item_id}
