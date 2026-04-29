from __future__ import annotations

import threading
import time
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.services.downloader import ResolvedSource
from app.services.event_bus import EventBus


def _login(client: TestClient, username: str = "admin", password: str = "admin1234") -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200


def test_create_job_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/jobs", json={"sources": ["https://example.com/video"]})
    assert response.status_code == 401


def test_create_job_expands_playlist_and_persists_flexible_config(client: TestClient, monkeypatch) -> None:
    _login(client)

    class StubDownloader:
        def resolve_sources(self, source_url: str, *, ytdlp_options):
            assert ytdlp_options == {"extractor_retries": 2}
            if "playlist" in source_url:
                return [
                    ResolvedSource(source_url="https://example.com/v1"),
                    ResolvedSource(source_url="https://example.com/v2"),
                ]
            return [ResolvedSource(source_url=source_url)]

    monkeypatch.setattr("app.api.routers.jobs.get_downloader", lambda: StubDownloader())

    response = client.post(
        "/api/jobs",
        json={
            "sources": ["https://example.com/playlist/abc"],
            "config": {
                "cookies_path": "D:/cookies/youtube.txt",
                "output_profile": "video_mp4",
                "ytdlp_options": {"extractor_retries": 2},
                "future_flag": {"enabled": True},
            },
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "queued"
    assert len(body["items"]) == 2
    assert [item["source_url"] for item in body["items"]] == ["https://example.com/v1", "https://example.com/v2"]
    assert body["config"]["cookies_path"] == "D:/cookies/youtube.txt"
    assert body["config"]["output_profile"] == "video_mp4"
    assert body["config"]["future_flag"] == {"enabled": True}


def test_job_ownership_is_isolated(client: TestClient, isolated_backend) -> None:
    db_module = isolated_backend["db_module"]
    models_module = __import__("app.db.models", fromlist=["User", "Job", "JobItem"])
    now = datetime.utcnow()

    with db_module.SessionLocal() as db:
        user = models_module.User(username="alice", password_hash=hash_password("alice1234"), role="user")
        db.add(user)
        db.flush()
        job = models_module.Job(user_id=user.id, status="queued", config_json="{}", created_at=now, updated_at=now)
        db.add(job)
        db.flush()
        db.add(
            models_module.JobItem(
                job_id=job.id,
                source_url="https://example.com/alice",
                status="queued",
                created_at=now,
                updated_at=now,
            )
        )
        db.commit()
        alien_job_id = job.id

    _login(client, username="admin", password="admin1234")
    response = client.get(f"/api/jobs/{alien_job_id}")
    assert response.status_code == 404


def test_cancel_job_updates_job_and_items(client: TestClient, monkeypatch) -> None:
    _login(client)

    class StubDownloader:
        def resolve_sources(self, source_url: str, *, ytdlp_options):
            return [ResolvedSource(source_url=source_url)]

    monkeypatch.setattr("app.api.routers.jobs.get_downloader", lambda: StubDownloader())
    created = client.post("/api/jobs", json={"sources": ["https://example.com/a"]})
    assert created.status_code == 201
    job_id = created.json()["id"]

    canceled = client.post(f"/api/jobs/{job_id}/cancel")
    assert canceled.status_code == 200
    assert canceled.json()["status"] == "canceled"

    fetched = client.get(f"/api/jobs/{job_id}")
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "canceled"
    assert fetched.json()["items"][0]["status"] == "canceled"

    canceled_item_id = fetched.json()["items"][0]["id"]
    retried = client.post(f"/api/items/{canceled_item_id}/retry")
    assert retried.status_code == 200
    assert retried.json()["status"] == "queued"


def test_retry_item_and_download(client: TestClient, isolated_backend, tmp_path: Path) -> None:
    _login(client)
    db_module = isolated_backend["db_module"]
    models_module = __import__("app.db.models", fromlist=["User", "Job", "JobItem"])
    now = datetime.utcnow()
    retry_output_file = tmp_path / "retry-file.bin"
    retry_output_file.write_bytes(b"old")
    part_file = Path(str(retry_output_file) + ".part")
    part_file.write_bytes(b"partial")
    ytdl_file = Path(str(retry_output_file) + ".ytdl")
    ytdl_file.write_text("tmp", encoding="utf-8")
    download_output_file = tmp_path / "file.bin"
    download_output_file.write_bytes(b"phase4")

    with db_module.SessionLocal() as db:
        admin = db.query(models_module.User).filter(models_module.User.username == "admin").one()
        job = models_module.Job(user_id=admin.id, status="queued", config_json="{}", created_at=now, updated_at=now)
        db.add(job)
        db.flush()
        retry_item = models_module.JobItem(
            job_id=job.id,
            source_url="https://example.com/retry",
            status="failed",
            output_path=str(retry_output_file),
            error_message="x",
            created_at=now,
            updated_at=now,
        )
        download_item = models_module.JobItem(
            job_id=job.id,
            source_url="https://example.com/download",
            status="completed",
            output_path=str(download_output_file),
            created_at=now,
            updated_at=now,
        )
        db.add(retry_item)
        db.add(download_item)
        db.commit()
        retry_item_id = retry_item.id
        download_item_id = download_item.id

    retried = client.post(f"/api/items/{retry_item_id}/retry")
    assert retried.status_code == 200
    assert retried.json()["status"] == "queued"
    assert not retry_output_file.exists()
    assert not part_file.exists()
    assert not ytdl_file.exists()

    downloaded = client.get(f"/api/items/{download_item_id}/download")
    assert downloaded.status_code == 200
    assert downloaded.content == b"phase4"


def test_events_stream_emits_user_event(client: TestClient) -> None:
    _login(client)
    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    user_id = me_response.json()["user"]["id"]

    event_bus = EventBus()
    event_bus.publish(user_id, {"type": "item_status", "item_id": 7, "status": "downloading"})

    import app.api.routers.events as events_router

    original_get_event_bus = events_router.get_event_bus
    events_router.get_event_bus = lambda: event_bus
    try:
        def publish_later() -> None:
            time.sleep(0.15)
            event_bus.publish(user_id, {"type": "item_status", "item_id": 7, "status": "downloading"})

        publisher = threading.Thread(target=publish_later, daemon=True)
        publisher.start()

        with client.stream("GET", "/api/events?once=true") as response:
            assert response.status_code == 200
            lines = []
            for line in response.iter_lines():
                if line:
                    lines.append(line)

        assert any("event: connected" in entry for entry in lines)
        assert any("downloading" in entry for entry in lines)
    finally:
        events_router.get_event_bus = original_get_event_bus
