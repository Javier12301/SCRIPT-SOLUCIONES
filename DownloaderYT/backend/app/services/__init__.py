from __future__ import annotations

from app.core.config import Settings
from app.db.database import SessionLocal
from app.services.downloader import DownloaderService
from app.services.event_bus import EventBus
from app.services.queue_worker import QueueWorker

_event_bus: EventBus | None = None
_downloader: DownloaderService | None = None
_queue_worker: QueueWorker | None = None


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def get_downloader() -> DownloaderService:
    global _downloader
    if _downloader is None:
        _downloader = DownloaderService()
    return _downloader


def get_queue_worker(settings: Settings) -> QueueWorker:
    global _queue_worker
    if _queue_worker is None:
        _queue_worker = QueueWorker(
            session_factory=SessionLocal,
            settings=settings,
            downloader=get_downloader(),
            event_bus=get_event_bus(),
        )
    return _queue_worker


def start_queue_worker(settings: Settings) -> QueueWorker:
    worker = get_queue_worker(settings)
    worker.start()
    return worker


def stop_queue_worker() -> None:
    global _queue_worker
    if _queue_worker is not None:
        _queue_worker.stop()
        _queue_worker = None
