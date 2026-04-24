"""tests for src/rss_wiki/main.py (FastAPI 앱 + lifespan + Jinja2 + 기본 /)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

from rss_wiki import db
from rss_wiki.main import create_app


class FakeScheduler:
    """BackgroundScheduler 와 호환되는 최소 더블."""

    def __init__(self) -> None:
        self.start_calls = 0
        self.shutdown_calls: list[bool] = []
        self.running = False

    def start(self) -> None:
        self.start_calls += 1
        self.running = True

    def shutdown(self, wait: bool = True) -> None:
        self.shutdown_calls.append(wait)
        self.running = False


def _make_app(tmp_path: Path, **overrides):
    defaults = dict(
        connection_factory=lambda: db.get_connection(tmp_path / "rss.db"),
        scheduler_factory=FakeScheduler,
        templates_dir=tmp_path / "templates",
    )
    defaults.update(overrides)
    return create_app(**defaults)


def test_create_app_returns_fastapi_instance(tmp_path: Path) -> None:
    app = _make_app(tmp_path)
    assert isinstance(app, FastAPI)


def test_index_returns_200(tmp_path: Path) -> None:
    app = _make_app(tmp_path)
    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert "RSS Wiki" in resp.text


def test_lifespan_initializes_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "rss.db"
    app = _make_app(tmp_path, connection_factory=lambda: db.get_connection(db_path))
    with TestClient(app) as client:
        client.get("/")

    conn = sqlite3.connect(db_path)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','virtual')"
            )
        }
    finally:
        conn.close()
    for expected in ("feeds", "categories", "articles", "wiki_pages", "job_logs"):
        assert expected in tables


def test_lifespan_starts_scheduler(tmp_path: Path) -> None:
    scheduler = FakeScheduler()
    app = _make_app(tmp_path, scheduler_factory=lambda: scheduler)
    with TestClient(app) as client:
        client.get("/")
        assert scheduler.start_calls == 1
        assert scheduler.running is True
    assert scheduler.shutdown_calls  # lifespan 종료 시 shutdown 호출


def test_lifespan_shutdown_passes_wait_false(tmp_path: Path) -> None:
    scheduler = FakeScheduler()
    app = _make_app(tmp_path, scheduler_factory=lambda: scheduler)
    with TestClient(app):
        pass
    assert scheduler.shutdown_calls == [False]


def test_app_state_exposes_templates_and_scheduler(tmp_path: Path) -> None:
    scheduler = FakeScheduler()
    app = _make_app(tmp_path, scheduler_factory=lambda: scheduler)
    assert isinstance(app.state.templates, Jinja2Templates)
    with TestClient(app):
        assert app.state.scheduler is scheduler


def test_start_scheduler_false_skips_start_and_shutdown(tmp_path: Path) -> None:
    scheduler = FakeScheduler()
    app = _make_app(
        tmp_path,
        scheduler_factory=lambda: scheduler,
        start_scheduler=False,
    )
    with TestClient(app):
        assert scheduler.start_calls == 0
    assert scheduler.shutdown_calls == []


def test_init_schema_is_called_with_connection(tmp_path: Path) -> None:
    captured: list[sqlite3.Connection] = []

    def fake_init(conn: sqlite3.Connection) -> None:
        captured.append(conn)

    app = _make_app(tmp_path, init_schema=fake_init)
    with TestClient(app):
        pass
    assert len(captured) == 1
    assert isinstance(captured[0], sqlite3.Connection)


def test_connection_is_closed_after_init_even_on_error(tmp_path: Path) -> None:
    class TrackingConnection:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    tracker = TrackingConnection()

    def failing_init(c: object) -> None:
        raise RuntimeError("boom")

    app = _make_app(
        tmp_path,
        connection_factory=lambda: tracker,
        init_schema=failing_init,
    )
    with pytest.raises(RuntimeError, match="boom"):
        with TestClient(app):
            pass
    assert tracker.closed is True


def test_module_level_app_is_fastapi() -> None:
    from rss_wiki import main as main_module

    assert isinstance(main_module.app, FastAPI)
