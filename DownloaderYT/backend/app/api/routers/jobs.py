from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.post("")
def create_job_placeholder() -> dict[str, str]:
    return {"message": "Fase 4: create job pendiente"}


@router.get("")
def list_jobs_placeholder() -> dict[str, str]:
    return {"message": "Fase 4: list jobs pendiente"}


@router.get("/{job_id}")
def get_job_placeholder(job_id: int) -> dict[str, str | int]:
    return {"message": "Fase 4: get job pendiente", "job_id": job_id}


@router.post("/{job_id}/cancel")
def cancel_job_placeholder(job_id: int) -> dict[str, str | int]:
    return {"message": "Fase 4: cancel job pendiente", "job_id": job_id}
