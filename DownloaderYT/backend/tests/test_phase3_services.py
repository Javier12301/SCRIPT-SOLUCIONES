from __future__ import annotations

import threading
import time
from pathlib import Path

from app.db.models import Job, JobItem, Setting, User
from app.services.downloader import DownloadResult, DownloaderService
from app.services.event_bus import EventBus
from app.services.queue_worker import QueueWorker


class FakeDownloader:
    def __init__(self, output_file: Path) -> None:
        self.output_file = output_file
        self.calls = 0

    def download(self, **kwargs) -> DownloadResult:
        self.calls += 1
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_file.write_text("content", encoding="utf-8")
        progress_hook = kwargs.get("progress_hook")
        if progress_hook:
            progress_hook({"downloaded_bytes": 10, "total_bytes": 10, "_speed_str": "1MiB/s", "_eta_str": "0s"})
        return DownloadResult(output_path=str(self.output_file), metadata={})


class SlowCancelableDownloader:
    def __init__(self, started_event: threading.Event) -> None:
        self.started_event = started_event

    def download(self, **kwargs) -> DownloadResult:
        progress_hook = kwargs.get("progress_hook")
        for idx in range(1, 60):
            if idx == 1:
                self.started_event.set()
            if progress_hook:
                progress_hook(
                    {
                        "status": "downloading",
                        "downloaded_bytes": idx * 1000,
                        "total_bytes": 100000,
                        "_speed_str": "1MiB/s",
                        "_eta_str": "1s",
                    }
                )
            time.sleep(0.03)
        raise AssertionError("Download should have been canceled before finishing")


def _seed_job(db_module, *, auto_transfer_enabled: bool, transfer_target_path: str | None) -> tuple[int, int]:
    with db_module.SessionLocal() as db:
        user = User(username="worker-user", password_hash="hash", role="user")
        db.add(user)
        db.flush()

        job = Job(user_id=user.id, status="queued", config_json="{}")
        db.add(job)
        db.flush()

        item = JobItem(job_id=job.id, source_url="https://example.com/video", status="queued")
        db.add(item)

        setting = Setting(
            user_id=user.id,
            auto_transfer_enabled=auto_transfer_enabled,
            transfer_target_path=transfer_target_path,
        )
        db.add(setting)
        db.commit()
        return user.id, item.id


def test_downloader_resolves_requested_filepath(monkeypatch) -> None:
    class StubYDL:
        def __init__(self, options):
            self.options = options

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, source_url, download):
            assert source_url == "https://example.com/one"
            assert download is True
            return {"requested_downloads": [{"filepath": "D:/tmp/video.mp4"}]}

    monkeypatch.setattr("app.services.downloader.yt_dlp.YoutubeDL", StubYDL)

    service = DownloaderService()
    result = service.download(source_url="https://example.com/one", output_template="%(title)s.%(ext)s")
    assert result.output_path.endswith("video.mp4")


def test_queue_worker_completes_item_without_transfer(isolated_backend, tmp_path: Path) -> None:
    db_module = isolated_backend["db_module"]
    config_module = isolated_backend["config_module"]
    db_module.init_db()
    user_id, item_id = _seed_job(db_module, auto_transfer_enabled=False, transfer_target_path=None)

    fake_downloader = FakeDownloader(tmp_path / "downloads" / "a.mp4")
    event_bus = EventBus()
    channel = event_bus.subscribe(user_id)
    worker = QueueWorker(
        session_factory=db_module.SessionLocal,
        settings=config_module.get_settings(),
        downloader=fake_downloader,
        event_bus=event_bus,
    )

    result = worker.process_once()
    assert result.processed is True
    assert result.status == "completed"
    assert fake_downloader.calls == 1

    with db_module.SessionLocal() as db:
        item = db.get(JobItem, item_id)
        assert item is not None
        assert item.status == "completed"
        assert item.output_path is not None

    collected_statuses = []
    while True:
        event = event_bus.poll(channel, timeout=0.01)
        if event is None:
            break
        collected_statuses.append(event["status"])
    assert "downloading" in collected_statuses
    assert "processing" in collected_statuses
    assert "completed" in collected_statuses


def test_queue_worker_sets_pending_when_unc_host_is_offline(isolated_backend, tmp_path: Path, monkeypatch) -> None:
    db_module = isolated_backend["db_module"]
    config_module = isolated_backend["config_module"]
    db_module.init_db()
    _, item_id = _seed_job(
        db_module,
        auto_transfer_enabled=True,
        transfer_target_path="\\\\offline-host\\videos",
    )

    fake_downloader = FakeDownloader(tmp_path / "downloads" / "offline.mp4")
    worker = QueueWorker(
        session_factory=db_module.SessionLocal,
        settings=config_module.get_settings(),
        downloader=fake_downloader,
        event_bus=EventBus(),
    )
    monkeypatch.setattr(worker, "_is_host_online", lambda host: False)

    result = worker.process_once()
    assert result.processed is True
    assert result.status == "pending_device_online"

    with db_module.SessionLocal() as db:
        item = db.get(JobItem, item_id)
        assert item is not None
        assert item.status == "pending_device_online"
        assert item.next_retry_at is not None


def test_queue_worker_transfers_and_deletes_local_file(isolated_backend, tmp_path: Path) -> None:
    db_module = isolated_backend["db_module"]
    config_module = isolated_backend["config_module"]
    db_module.init_db()
    transfer_dir = tmp_path / "target"
    _, item_id = _seed_job(
        db_module,
        auto_transfer_enabled=True,
        transfer_target_path=str(transfer_dir),
    )

    local_file = tmp_path / "downloads" / "to-move.mp4"
    fake_downloader = FakeDownloader(local_file)
    worker = QueueWorker(
        session_factory=db_module.SessionLocal,
        settings=config_module.get_settings(),
        downloader=fake_downloader,
        event_bus=EventBus(),
    )

    result = worker.process_once()
    assert result.processed is True
    assert result.status == "completed"
    assert (transfer_dir / "to-move.mp4").exists()
    assert not local_file.exists()

    with db_module.SessionLocal() as db:
        item = db.get(JobItem, item_id)
        assert item is not None
        assert item.status == "completed"


def test_queue_worker_stops_active_download_when_cancel_requested(isolated_backend) -> None:
    db_module = isolated_backend["db_module"]
    config_module = isolated_backend["config_module"]
    db_module.init_db()
    _, item_id = _seed_job(
        db_module,
        auto_transfer_enabled=False,
        transfer_target_path=None,
    )

    settings = config_module.get_settings()
    settings.worker_cancel_check_interval_seconds = 0.05
    settings.worker_cancel_check_progress_step = 1
    settings.worker_progress_flush_interval_seconds = 0.05

    started_event = threading.Event()
    worker = QueueWorker(
        session_factory=db_module.SessionLocal,
        settings=settings,
        downloader=SlowCancelableDownloader(started_event=started_event),
        event_bus=EventBus(),
    )

    result_holder: dict[str, object] = {}

    def run_worker_once() -> None:
        result_holder["result"] = worker.process_once()

    worker_thread = threading.Thread(target=run_worker_once, daemon=True)
    worker_thread.start()
    assert started_event.wait(timeout=2), "Download never started"

    with db_module.SessionLocal() as db:
        item = db.get(JobItem, item_id)
        assert item is not None
        item.cancel_requested = True
        item.status = "canceled"
        db.commit()

    worker_thread.join(timeout=5)
    assert not worker_thread.is_alive(), "Worker did not stop after cancel request"

    result = result_holder.get("result")
    assert result is not None
    assert result.status == "canceled"

    with db_module.SessionLocal() as db:
        item = db.get(JobItem, item_id)
        assert item is not None
        assert item.status == "canceled"
        assert item.cancel_requested is True


def test_build_ytdlp_options_supports_output_profiles(isolated_backend) -> None:
    config_module = isolated_backend["config_module"]
    db_module = isolated_backend["db_module"]
    worker = QueueWorker(
        session_factory=db_module.SessionLocal,
        settings=config_module.get_settings(),
        downloader=FakeDownloader(Path("dummy.mp4")),
        event_bus=EventBus(),
    )

    video_opts = worker._build_ytdlp_options({"output_profile": "video_mp4"})
    assert video_opts["format"] == "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    assert video_opts["merge_output_format"] == "mp4"
    assert any(pp.get("key") == "FFmpegVideoRemuxer" for pp in video_opts.get("postprocessors", []))

    audio_opts = worker._build_ytdlp_options({"output_profile": "audio_mp3"})
    assert any(pp.get("key") == "FFmpegExtractAudio" for pp in audio_opts.get("postprocessors", []))

    custom_video_opts = worker._build_ytdlp_options(
        {
            "output_profile": "video_mp4",
            "ytdlp_options": {"format": "best[height<=720]"},
        }
    )
    assert custom_video_opts["format"] == "best[height<=720]"


def test_normalize_error_message_removes_ansi(isolated_backend) -> None:
    config_module = isolated_backend["config_module"]
    db_module = isolated_backend["db_module"]
    worker = QueueWorker(
        session_factory=db_module.SessionLocal,
        settings=config_module.get_settings(),
        downloader=FakeDownloader(Path("dummy.mp4")),
        event_bus=EventBus(),
    )
    cleaned = worker._normalize_error_message("\u001b[0;31mERROR:\u001b[0m failure")
    assert cleaned == "ERROR: failure"
