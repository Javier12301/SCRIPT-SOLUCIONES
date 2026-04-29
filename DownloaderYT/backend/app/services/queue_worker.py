from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from threading import Event, Thread
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.db.models import JobItem, Setting
from app.services.downloader import DownloaderService
from app.services.event_bus import EventBus


class DownloadCanceledByUser(RuntimeError):
    pass


@dataclass
class WorkerCycleResult:
    processed: bool
    item_id: int | None = None
    status: str | None = None
    error_message: str | None = None


class QueueWorker:
    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        settings: Settings,
        downloader: DownloaderService,
        event_bus: EventBus,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings
        self._downloader = downloader
        self._event_bus = event_bus
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._cancel_check_cache: dict[int, float] = {}
        self._cancel_progress_bucket_cache: dict[int, int] = {}
        self._cancel_requested_cache: dict[int, bool] = {}
        self._progress_flush_cache: dict[int, float] = {}

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._run_loop, name="queue-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            result = self.process_once()
            if not result.processed:
                time.sleep(0.5)

    def process_once(self) -> WorkerCycleResult:
        with self._session_factory() as db:
            item = self._pick_next_item(db)
            if item is None:
                return WorkerCycleResult(processed=False)

            try:
                return self._process_item(db, item)
            except DownloadCanceledByUser:
                db.refresh(item)
                item.status = "canceled"
                item.error_message = "Canceled by user"
                item.updated_at = datetime.utcnow()
                db.commit()
                self._clear_runtime_caches_for_item(item.id)
                self._publish_item_event(item)
                return WorkerCycleResult(processed=True, item_id=item.id, status=item.status, error_message=item.error_message)
            except Exception as exc:
                item.status = "failed"
                item.error_message = self._normalize_error_message(str(exc))
                item.updated_at = datetime.utcnow()
                db.commit()
                self._clear_runtime_caches_for_item(item.id)
                self._publish_item_event(item)
                return WorkerCycleResult(
                    processed=True,
                    item_id=item.id,
                    status=item.status,
                    error_message=item.error_message,
                )

    def _pick_next_item(self, db: Session) -> JobItem | None:
        now = datetime.utcnow()
        query = (
            select(JobItem)
            .where(
                (JobItem.status == "queued")
                | (
                    (JobItem.status == "pending_device_online")
                    & ((JobItem.next_retry_at.is_(None)) | (JobItem.next_retry_at <= now))
                )
            )
            .order_by(JobItem.created_at.asc())
            .limit(1)
        )
        return db.execute(query).scalar_one_or_none()

    def _process_item(self, db: Session, item: JobItem) -> WorkerCycleResult:
        if item.cancel_requested or item.status == "canceled":
            item.status = "canceled"
            item.error_message = "Canceled by user"
            item.updated_at = datetime.utcnow()
            db.commit()
            self._clear_runtime_caches_for_item(item.id)
            self._publish_item_event(item)
            return WorkerCycleResult(processed=True, item_id=item.id, status=item.status)

        setting = self._get_user_setting(db, item)
        job_config = parse_job_config(item.job.config_json)
        ytdlp_options = self._build_ytdlp_options(job_config)

        item.status = "downloading"
        item.error_message = None
        item.updated_at = datetime.utcnow()
        db.commit()
        self._publish_item_event(item)

        download_root = self._resolve_download_root(setting=setting)
        download_root.mkdir(parents=True, exist_ok=True)
        output_template = str(download_root / f"job{item.job_id}_item{item.id}-%(title)s.%(ext)s")

        result = self._downloader.download(
            source_url=item.source_url,
            output_template=output_template,
            ytdlp_options=ytdlp_options,
            progress_hook=self._build_progress_hook(item.id),
            postprocessor_hook=self._build_postprocessor_hook(item.id),
        )

        db.refresh(item)
        if item.cancel_requested or item.status == "canceled":
            item.status = "canceled"
            item.error_message = "Canceled by user"
            item.updated_at = datetime.utcnow()
            db.commit()
            self._clear_runtime_caches_for_item(item.id)
            self._publish_item_event(item)
            return WorkerCycleResult(processed=True, item_id=item.id, status=item.status)

        item.status = "processing"
        item.output_path = result.output_path
        item.updated_at = datetime.utcnow()
        db.commit()
        self._publish_item_event(item)

        if not setting or not setting.auto_transfer_enabled or not setting.transfer_target_path:
            db.refresh(item)
            if item.cancel_requested or item.status == "canceled":
                item.status = "canceled"
                item.error_message = "Canceled by user"
                item.updated_at = datetime.utcnow()
                db.commit()
                self._clear_runtime_caches_for_item(item.id)
                self._publish_item_event(item)
                return WorkerCycleResult(processed=True, item_id=item.id, status=item.status)
            item.status = "completed"
            item.updated_at = datetime.utcnow()
            db.commit()
            self._clear_runtime_caches_for_item(item.id)
            self._publish_item_event(item)
            return WorkerCycleResult(processed=True, item_id=item.id, status=item.status)

        return self._run_transfer_flow(db=db, item=item, transfer_target=setting.transfer_target_path)

    def _run_transfer_flow(self, *, db: Session, item: JobItem, transfer_target: str) -> WorkerCycleResult:
        if item.cancel_requested or item.status == "canceled":
            item.status = "canceled"
            item.error_message = "Canceled by user"
            item.updated_at = datetime.utcnow()
            db.commit()
            self._clear_runtime_caches_for_item(item.id)
            self._publish_item_event(item)
            return WorkerCycleResult(processed=True, item_id=item.id, status=item.status)

        host = self._extract_unc_host(transfer_target)
        if host and not self._is_host_online(host):
            item.status = "pending_device_online"
            item.next_retry_at = datetime.utcnow() + timedelta(seconds=self._settings.transfer_retry_seconds)
            item.updated_at = datetime.utcnow()
            db.commit()
            self._publish_item_event(item)
            return WorkerCycleResult(processed=True, item_id=item.id, status=item.status)

        item.status = "transferring"
        item.updated_at = datetime.utcnow()
        db.commit()
        self._publish_item_event(item)

        if not item.output_path:
            raise RuntimeError("Output path missing before transfer")

        source_file = Path(item.output_path)
        if not source_file.exists():
            raise RuntimeError(f"Downloaded file not found: {source_file}")

        target_dir = Path(transfer_target)
        target_dir.mkdir(parents=True, exist_ok=True)
        destination = target_dir / source_file.name

        shutil.copy2(source_file, destination)
        source_file.unlink(missing_ok=True)

        db.refresh(item)
        if item.cancel_requested or item.status == "canceled":
            item.status = "canceled"
            item.error_message = "Canceled by user"
            item.updated_at = datetime.utcnow()
            db.commit()
            self._clear_runtime_caches_for_item(item.id)
            self._publish_item_event(item)
            return WorkerCycleResult(processed=True, item_id=item.id, status=item.status)

        item.status = "completed"
        item.next_retry_at = None
        item.updated_at = datetime.utcnow()
        db.commit()
        self._clear_runtime_caches_for_item(item.id)
        self._publish_item_event(item)
        return WorkerCycleResult(processed=True, item_id=item.id, status=item.status)

    def _resolve_download_root(self, *, setting: Setting | None) -> Path:
        if setting and setting.download_root_override:
            return Path(setting.download_root_override)
        return Path(self._settings.downloads_root)

    @staticmethod
    def _extract_unc_host(transfer_target: str) -> str | None:
        if transfer_target.startswith("\\\\"):
            remainder = transfer_target[2:]
            host = remainder.split("\\", 1)[0].strip()
            return host or None
        return None

    @staticmethod
    def _is_host_online(host: str) -> bool:
        process = subprocess.run(
            ["ping", "-n", "1", "-w", "1000", host],
            capture_output=True,
            text=True,
            check=False,
        )
        return process.returncode == 0

    @staticmethod
    def _get_user_setting(db: Session, item: JobItem) -> Setting | None:
        user_id = item.job.user_id
        query = select(Setting).where(Setting.user_id == user_id).limit(1)
        return db.execute(query).scalar_one_or_none()

    def _publish_item_event(self, item: JobItem) -> None:
        self._event_bus.publish(
            item.job.user_id,
            {
                "type": "item_status",
                "item_id": item.id,
                "job_id": item.job_id,
                "status": item.status,
                "progress_pct": item.progress_pct,
                "downloaded_bytes": item.downloaded_bytes,
                "total_bytes": item.total_bytes,
                "speed": item.speed,
                "eta": item.eta,
                "error_message": item.error_message,
                "next_retry_at": item.next_retry_at.isoformat() if item.next_retry_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            },
        )

    def _build_progress_hook(self, item_id: int):
        def hook(data: dict[str, Any]) -> None:
            downloaded_bytes = int(data.get("downloaded_bytes") or 0)
            total_bytes_value = data.get("total_bytes") or data.get("total_bytes_estimate")
            total_bytes = int(total_bytes_value) if total_bytes_value is not None else None
            progress_pct = 0.0
            if total_bytes and total_bytes > 0:
                progress_pct = round((downloaded_bytes / total_bytes) * 100, 2)
            speed = self._to_text(data.get("_speed_str"))
            eta = self._to_text(data.get("_eta_str"))
            status_value = self._to_text(data.get("status")) or ""

            now_monotonic = time.monotonic()
            should_poll_cancel = self._should_poll_cancel(
                item_id=item_id,
                now_monotonic=now_monotonic,
                progress_pct=progress_pct,
            )
            should_flush_progress = self._should_flush_progress(item_id=item_id, now_monotonic=now_monotonic)
            should_sync = should_poll_cancel or should_flush_progress or status_value.lower() == "finished"
            if not should_sync:
                return

            with self._session_factory() as db:
                item = db.get(JobItem, item_id)
                if item is None:
                    return
                item.downloaded_bytes = downloaded_bytes
                item.total_bytes = total_bytes
                item.progress_pct = progress_pct
                item.speed = speed
                item.eta = eta
                item.updated_at = datetime.utcnow()

                cancel_requested = item.cancel_requested or item.status == "canceled"
                if should_poll_cancel:
                    self._cancel_requested_cache[item_id] = cancel_requested
                elif item_id not in self._cancel_requested_cache:
                    self._cancel_requested_cache[item_id] = cancel_requested

                db.commit()
                self._publish_item_event(item)

            if self._cancel_requested_cache.get(item_id, False):
                raise DownloadCanceledByUser("Download canceled by user")

        return hook

    def _build_postprocessor_hook(self, item_id: int):
        def hook(data: dict[str, Any]) -> None:
            status_value = self._to_text(data.get("status")) or ""
            with self._session_factory() as db:
                item = db.get(JobItem, item_id)
                if item is None:
                    return
                if item.cancel_requested or item.status == "canceled":
                    raise DownloadCanceledByUser("Download canceled by user")
                if status_value.lower() == "started":
                    item.status = "processing"
                    item.updated_at = datetime.utcnow()
                    db.commit()
                    self._publish_item_event(item)

        return hook

    @staticmethod
    def _to_text(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _build_ytdlp_options(job_config: dict[str, Any]) -> dict[str, Any]:
        options: dict[str, Any] = {"noplaylist": True}
        raw_options = job_config.get("ytdlp_options")
        if isinstance(raw_options, dict):
            options.update(raw_options)
        cookies_path = job_config.get("cookies_path")
        if isinstance(cookies_path, str) and cookies_path.strip():
            options["cookiefile"] = cookies_path.strip()

        output_profile = job_config.get("output_profile")
        if output_profile == "video_mp4":
            if not options.get("format"):
                options["format"] = "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            options["merge_output_format"] = "mp4"
            postprocessors = list(options.get("postprocessors", []))
            postprocessors.append({"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"})
            options["postprocessors"] = postprocessors
        elif output_profile == "audio_mp3":
            postprocessors = list(options.get("postprocessors", []))
            postprocessors.append(
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            )
            options["postprocessors"] = postprocessors
        return options

    def _should_poll_cancel(self, *, item_id: int, now_monotonic: float, progress_pct: float) -> bool:
        last_check = self._cancel_check_cache.get(item_id)
        progress_step = max(1, int(self._settings.worker_cancel_check_progress_step))
        bucket = int(progress_pct // progress_step)
        last_bucket = self._cancel_progress_bucket_cache.get(item_id, -1)

        interval_due = (
            last_check is None
            or (now_monotonic - last_check) >= float(self._settings.worker_cancel_check_interval_seconds)
        )
        bucket_changed = bucket > last_bucket
        should_poll = interval_due or bucket_changed
        if should_poll:
            self._cancel_check_cache[item_id] = now_monotonic
            self._cancel_progress_bucket_cache[item_id] = bucket
        return should_poll

    def _should_flush_progress(self, *, item_id: int, now_monotonic: float) -> bool:
        last_flush = self._progress_flush_cache.get(item_id)
        should_flush = (
            last_flush is None
            or (now_monotonic - last_flush) >= float(self._settings.worker_progress_flush_interval_seconds)
        )
        if should_flush:
            self._progress_flush_cache[item_id] = now_monotonic
        return should_flush

    def _clear_runtime_caches_for_item(self, item_id: int) -> None:
        self._cancel_check_cache.pop(item_id, None)
        self._cancel_progress_bucket_cache.pop(item_id, None)
        self._cancel_requested_cache.pop(item_id, None)
        self._progress_flush_cache.pop(item_id, None)

    @staticmethod
    def _normalize_error_message(message: str) -> str:
        ansi_pattern = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
        return ansi_pattern.sub("", message).strip()


def parse_job_config(config_json: str) -> dict[str, Any]:
    try:
        raw = json.loads(config_json or "{}")
    except json.JSONDecodeError:
        return {}
    if isinstance(raw, dict):
        return raw
    return {}
