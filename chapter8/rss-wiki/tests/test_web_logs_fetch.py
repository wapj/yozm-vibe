"""로그 페이지 / 수동 수집 라우트 테스트 (PRD §9, §10, TASKS.md §6).

- GET /logs : `job_logs` 최근 N건 (기본 200)을 started_at 내림차순으로 렌더.
- POST /api/fetch : 수동 수집 트리거. 이미 사이클 진행 중이면 409.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rss_wiki import config, db, scheduler
from rss_wiki.main import create_app
from rss_wiki.pipeline.cycle import CycleResult


class _FakeScheduler:
    def __init__(self) -> None:
        self.running = False

    def start(self) -> None:
        self.running = True

    def shutdown(self, wait: bool = True) -> None:
        self.running = False


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "rss.db"
    app = create_app(
        connection_factory=lambda: db.get_connection(db_path),
        scheduler_factory=_FakeScheduler,
        templates_dir=tmp_path / "templates",
        start_scheduler=False,
    )
    with TestClient(app) as c:
        c.db_path = db_path  # type: ignore[attr-defined]
        yield c


def _insert_log(
    db_path: Path,
    *,
    job_type: str,
    status: str,
    started_at: str,
    target_ref: str | None = None,
    error_message: str | None = None,
    finished_at: str | None = None,
    attempt_count: int = 1,
) -> int:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            """
            INSERT INTO job_logs (
                job_type, target_ref, status, error_message,
                attempt_count, started_at, finished_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_type,
                target_ref,
                status,
                error_message,
                attempt_count,
                started_at,
                finished_at,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


# ---------- GET /logs ----------


def test_logs_empty_renders_200(client: TestClient) -> None:
    resp = client.get("/logs")
    assert resp.status_code == 200


def test_logs_shows_job_type_and_status(client: TestClient) -> None:
    _insert_log(
        client.db_path,  # type: ignore[attr-defined]
        job_type="fetch_feed",
        status="ok",
        started_at="2026-04-25T10:00:00",
    )
    _insert_log(
        client.db_path,  # type: ignore[attr-defined]
        job_type="summarize",
        status="failed",
        error_message="LLM timeout exceeded",
        started_at="2026-04-25T10:05:00",
    )
    resp = client.get("/logs")
    assert resp.status_code == 200
    assert "fetch_feed" in resp.text
    assert "summarize" in resp.text
    assert "failed" in resp.text
    assert "LLM timeout exceeded" in resp.text


def test_logs_ordered_most_recent_first(client: TestClient) -> None:
    _insert_log(
        client.db_path,  # type: ignore[attr-defined]
        job_type="uniquejob_older",
        status="ok",
        started_at="2026-04-25T09:00:00",
    )
    _insert_log(
        client.db_path,  # type: ignore[attr-defined]
        job_type="uniquejob_newer",
        status="ok",
        started_at="2026-04-25T11:00:00",
    )
    resp = client.get("/logs")
    assert resp.status_code == 200
    assert resp.text.find("uniquejob_newer") < resp.text.find("uniquejob_older")


def test_logs_limits_to_200_entries(client: TestClient) -> None:
    assert config.JOB_LOG_LIST_LIMIT == 200

    conn = sqlite3.connect(client.db_path)  # type: ignore[attr-defined]
    try:
        for i in range(250):
            started_at = f"2026-04-25T{i // 60:02d}:{i % 60:02d}:00"
            conn.execute(
                """
                INSERT INTO job_logs (job_type, status, started_at)
                VALUES (?, ?, ?)
                """,
                (f"logjob_{i:03d}", "ok", started_at),
            )
        conn.commit()
    finally:
        conn.close()

    resp = client.get("/logs")
    assert resp.status_code == 200
    # 최신 200건(logjob_050 ~ logjob_249)이 포함되고, 오래된 50건은 제외.
    assert "logjob_249" in resp.text
    assert "logjob_050" in resp.text
    assert "logjob_049" not in resp.text
    assert "logjob_000" not in resp.text


def test_logs_shows_target_ref(client: TestClient) -> None:
    _insert_log(
        client.db_path,  # type: ignore[attr-defined]
        job_type="rebuild_wiki",
        status="ok",
        target_ref="42",
        started_at="2026-04-25T12:00:00",
    )
    resp = client.get("/logs")
    assert resp.status_code == 200
    assert "rebuild_wiki" in resp.text
    assert "42" in resp.text


# ---------- POST /api/fetch ----------


def test_api_fetch_runs_cycle_and_returns_summary(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict] = []

    async def fake_run_fetch_cycle(**kwargs):
        calls.append(kwargs)
        return CycleResult(
            feeds_attempted=3,
            feeds_succeeded=2,
            feeds_failed=1,
            new_articles=5,
            ok_articles=4,
            failed_articles=1,
            affected_category_ids=[7, 9],
            rebuilt_category_ids=[7, 9],
        )

    monkeypatch.setattr(
        "rss_wiki.web.routes.run_fetch_cycle", fake_run_fetch_cycle
    )
    resp = client.post("/api/fetch")
    assert resp.status_code == 202
    data = resp.json()
    assert data["feeds_attempted"] == 3
    assert data["feeds_succeeded"] == 2
    assert data["feeds_failed"] == 1
    assert data["new_articles"] == 5
    assert data["ok_articles"] == 4
    assert data["failed_articles"] == 1
    assert data["affected_category_ids"] == [7, 9]
    assert data["rebuilt_category_ids"] == [7, 9]
    assert len(calls) == 1
    # 앱의 connection_factory 가 실제로 전달되었는지 확인.
    assert "connection_factory" in calls[0]
    assert callable(calls[0]["connection_factory"])


def test_api_fetch_returns_409_when_busy(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def busy_runner(**kwargs):
        raise scheduler.FetchBusyError("already running")

    monkeypatch.setattr("rss_wiki.web.routes.run_fetch_cycle", busy_runner)
    resp = client.post("/api/fetch")
    assert resp.status_code == 409
