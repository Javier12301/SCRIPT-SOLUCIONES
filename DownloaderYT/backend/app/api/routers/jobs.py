from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import db_session, get_current_user
from app.db.models import Job, JobItem, User
from app.schemas.job import JobCancelResponse, JobCreateRequest, JobItemResponse, JobListResponse, JobResponse
from app.services import get_downloader
from app.services.downloader import DownloaderService

router = APIRouter()

ACTIVE_STATUSES_FOR_CANCEL = {"pending", "queued", "downloading", "processing", "pending_device_online", "transferring"}


def _to_job_item_response(item: JobItem) -> JobItemResponse:
    return JobItemResponse(
        id=item.id,
        job_id=item.job_id,
        source_url=item.source_url,
        status=item.status,
        progress_pct=item.progress_pct,
        downloaded_bytes=item.downloaded_bytes,
        total_bytes=item.total_bytes,
        speed=item.speed,
        eta=item.eta,
        output_path=item.output_path,
        error_message=item.error_message,
        next_retry_at=item.next_retry_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _to_job_response(job: Job) -> JobResponse:
    config = {}
    try:
        parsed = json.loads(job.config_json or "{}")
        if isinstance(parsed, dict):
            config = parsed
    except json.JSONDecodeError:
        config = {}

    sorted_items = sorted(job.items, key=lambda item: item.id)
    return JobResponse(
        id=job.id,
        user_id=job.user_id,
        status=job.status,
        config=config,
        created_at=job.created_at,
        updated_at=job.updated_at,
        items=[_to_job_item_response(item) for item in sorted_items],
    )


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreateRequest,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    downloader: DownloaderService = get_downloader()

    config_dict = payload.config.model_dump(mode="json")
    ytdlp_options = config_dict.get("ytdlp_options")
    if not isinstance(ytdlp_options, dict):
        ytdlp_options = {}

    resolved_sources: list[str] = []
    for source in payload.sources:
        for entry in downloader.resolve_sources(source, ytdlp_options=ytdlp_options):
            resolved_sources.append(entry.source_url)

    if not resolved_sources:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No resolvable sources found")

    now = datetime.utcnow()
    job = Job(
        user_id=current_user.id,
        status="queued",
        config_json=json.dumps(config_dict),
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    db.flush()

    for source_url in resolved_sources:
        item = JobItem(
            job_id=job.id,
            source_url=source_url,
            status="queued",
            created_at=now,
            updated_at=now,
        )
        db.add(item)

    db.commit()

    created_job = db.execute(
        select(Job).where(Job.id == job.id).options(selectinload(Job.items))
    ).scalar_one()
    return _to_job_response(created_job)


@router.get("", response_model=JobListResponse)
def list_jobs(
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> JobListResponse:
    jobs = db.execute(
        select(Job)
        .where(Job.user_id == current_user.id)
        .order_by(Job.created_at.desc())
        .options(selectinload(Job.items))
    ).scalars().all()
    return JobListResponse(jobs=[_to_job_response(job) for job in jobs])


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    job = db.execute(
        select(Job)
        .where(Job.id == job_id, Job.user_id == current_user.id)
        .options(selectinload(Job.items))
    ).scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return _to_job_response(job)


@router.post("/{job_id}/cancel", response_model=JobCancelResponse)
def cancel_job(
    job_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> JobCancelResponse:
    job = db.execute(
        select(Job)
        .where(Job.id == job_id, Job.user_id == current_user.id)
        .options(selectinload(Job.items))
    ).scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    now = datetime.utcnow()
    job.status = "canceled"
    job.updated_at = now
    for item in job.items:
        if item.status in ACTIVE_STATUSES_FOR_CANCEL:
            item.cancel_requested = True
            item.status = "canceled"
            item.error_message = "Canceled by user"
            item.updated_at = now

    db.commit()
    return JobCancelResponse(message="job canceled", job_id=job.id, status=job.status)
