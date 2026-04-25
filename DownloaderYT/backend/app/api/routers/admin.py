from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import require_admin

router = APIRouter()


@router.post("/update-extractor")
def update_extractor_placeholder(_: object = Depends(require_admin)) -> dict[str, str]:
    return {"message": "Fase 4: admin update extractor pendiente"}
