from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import db_session, get_current_user
from app.db.models import Job, JobItem, User
from app.schemas.item import ItemRetryResponse

router = APIRouter()

RETRYABLE_STATUSES = {"failed", "canceled", "pending_device_online"}


def _get_owned_item(db: Session, *, item_id: int, user_id: int) -> JobItem | None:
    return db.execute(
        select(JobItem)
        .join(Job, JobItem.job_id == Job.id)
        .where(JobItem.id == item_id, Job.user_id == user_id)
        .options(selectinload(JobItem.job))
    ).scalar_one_or_none()


def _cleanup_item_artifacts(item: JobItem) -> None:
    files_to_remove: set[Path] = set()

    if item.output_path:
        output_path = Path(item.output_path)
        files_to_remove.add(output_path)
        files_to_remove.add(Path(str(output_path) + ".part"))
        files_to_remove.add(Path(str(output_path) + ".ytdl"))

        parent = output_path.parent
        stem = output_path.stem
        if parent.exists():
            for candidate in parent.glob(f"{stem}*"):
                if candidate.is_file():
                    files_to_remove.add(candidate)

    for file_path in files_to_remove:
        try:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
        except OSError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Failed to cleanup retry artifacts: {file_path} ({exc})",
            ) from exc


@router.post("/{item_id}/retry", response_model=ItemRetryResponse)
def retry_item(
    item_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> ItemRetryResponse:
    item = _get_owned_item(db, item_id=item_id, user_id=current_user.id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if item.status not in RETRYABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Item cannot be retried from status '{item.status}'",
        )

    _cleanup_item_artifacts(item)

    now = datetime.utcnow()
    item.status = "queued"
    item.cancel_requested = False
    item.output_path = None
    item.error_message = None
    item.next_retry_at = None
    item.progress_pct = 0.0
    item.downloaded_bytes = 0
    item.total_bytes = None
    item.speed = None
    item.eta = None
    item.updated_at = now

    if item.job.status == "canceled":
        item.job.status = "queued"
        item.job.updated_at = now

    db.commit()
    return ItemRetryResponse(message="item queued for retry", item_id=item.id, status=item.status, updated_at=item.updated_at)


@router.get("/{item_id}/download")
def download_item(
    item_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_current_user),
):
    item = _get_owned_item(db, item_id=item_id, user_id=current_user.id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if item.status != "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Item is not completed yet")

    if not item.output_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output file not available")

    output_file = Path(item.output_path)
    if not output_file.exists() or not output_file.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output file not found")

    return FileResponse(path=output_file, filename=output_file.name, media_type="application/octet-stream")
