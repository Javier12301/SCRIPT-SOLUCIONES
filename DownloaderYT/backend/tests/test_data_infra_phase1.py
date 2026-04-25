from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect, select

from app.db import models


def test_init_db_creates_sqlite_file_and_expected_tables(isolated_backend: dict[str, object]) -> None:
    db_path = isolated_backend["db_path"]
    db_module = isolated_backend["db_module"]
    db_module.init_db()

    assert isinstance(db_path, Path)
    assert db_path.exists()

    table_names = set(inspect(db_module.engine).get_table_names())
    expected_tables = {"users", "sessions", "jobs", "job_items", "settings"}
    assert expected_tables.issubset(table_names)


def test_sqlite_pragmas_are_applied_on_connections(isolated_backend: dict[str, object]) -> None:
    db_module = isolated_backend["db_module"]

    with db_module.engine.connect() as connection:
        journal_mode = str(connection.exec_driver_sql("PRAGMA journal_mode;").scalar()).lower()
        synchronous = int(connection.exec_driver_sql("PRAGMA synchronous;").scalar())
        busy_timeout = int(connection.exec_driver_sql("PRAGMA busy_timeout;").scalar())
        foreign_keys = int(connection.exec_driver_sql("PRAGMA foreign_keys;").scalar())

    assert journal_mode == "wal"
    assert synchronous == 1  # NORMAL
    assert busy_timeout == 5000
    assert foreign_keys == 1


def test_settings_take_values_from_env_in_tests(isolated_backend: dict[str, object]) -> None:
    config_module = isolated_backend["config_module"]
    db_path = isolated_backend["db_path"]
    settings = config_module.get_settings()

    assert settings.env == "test"
    assert Path(settings.db_path).name == db_path.name


def test_bootstrap_admin_is_created_on_init(isolated_backend: dict[str, object]) -> None:
    db_module = isolated_backend["db_module"]

    db_module.init_db()
    with db_module.SessionLocal() as db:
        admin_user = db.execute(select(models.User).where(models.User.username == "admin")).scalar_one_or_none()

    assert admin_user is not None
    assert admin_user.role == "admin"
