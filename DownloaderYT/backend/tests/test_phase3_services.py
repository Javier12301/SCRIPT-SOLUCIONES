from __future__ import annotations

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

