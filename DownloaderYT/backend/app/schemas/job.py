from __future__ import annotations

from datetime import datetime
from typing import Literal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    cookies_path: str | None = None
    output_profile: Literal["video_mp4", "audio_mp3"] | None = None
    ytdlp_options: dict[str, Any] = Field(default_factory=dict)


class JobCreateRequest(BaseModel):
    sources: list[str] = Field(min_length=1)
    config: JobConfig = Field(default_factory=JobConfig)


class JobItemResponse(BaseModel):
    id: int
    job_id: int
    source_url: str
    status: str
    progress_pct: float
    downloaded_bytes: int
    total_bytes: int | None
    speed: str | None
    eta: str | None
    output_path: str | None
    error_message: str | None
    next_retry_at: datetime | None
    created_at: datetime
    updated_at: datetime


class JobResponse(BaseModel):
    id: int
    user_id: int
    status: str
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    items: list[JobItemResponse]


class JobListResponse(BaseModel):
    jobs: list[JobResponse]


class JobCancelResponse(BaseModel):
    message: str
    job_id: int
    status: str
