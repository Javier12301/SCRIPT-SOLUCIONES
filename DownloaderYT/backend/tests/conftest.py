from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

MODULES_TO_RELOAD = (
    "app.api.dependencies",
    "app.api.routers.admin",
    "app.api.routers.auth",
    "app.api.routers.events",
    "app.api.routers.items",
    "app.api.routers.jobs",
    "app.api.routers",
    "app.main",
    "app.db.session_store",
    "app.db.models",
    "app.db.database",
    "app.services.queue_worker",
    "app.services.event_bus",
    "app.services.downloader",
    "app.services",
    "app.core.security",
    "app.core.config",
)


def _reload_backend_modules() -> tuple[object, object, object]:
    for module_name in MODULES_TO_RELOAD:
        sys.modules.pop(module_name, None)

    config_module = importlib.import_module("app.core.config")
    config_module.get_settings.cache_clear()
    db_module = importlib.import_module("app.db.database")
    importlib.import_module("app.db.models")
    main_module = importlib.import_module("app.main")
    return main_module, db_module, config_module


@pytest.fixture()
def isolated_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    db_path = tmp_path / "test_app.db"
    monkeypatch.setenv("APP_DB_PATH", str(db_path))
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("APP_CORS_ORIGINS", '["http://localhost:5173","http://127.0.0.1:5173"]')
    monkeypatch.setenv("APP_BOOTSTRAP_ADMIN_ENABLED", "true")
    monkeypatch.setenv("APP_BOOTSTRAP_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("APP_BOOTSTRAP_ADMIN_PASSWORD", "admin1234")

    main_module, db_module, config_module = _reload_backend_modules()
    yield {
        "main_module": main_module,
        "db_module": db_module,
        "config_module": config_module,
        "db_path": db_path,
    }

    config_module.get_settings.cache_clear()
    for module_name in MODULES_TO_RELOAD:
        sys.modules.pop(module_name, None)


@pytest.fixture()
def app_instance(isolated_backend: dict[str, object]):
    main_module = isolated_backend["main_module"]
    return main_module.create_app()


@pytest.fixture()
def client(app_instance, isolated_backend: dict[str, object]):
    db_module = isolated_backend["db_module"]
    db_module.init_db()
    with TestClient(app_instance) as test_client:
        yield test_client
