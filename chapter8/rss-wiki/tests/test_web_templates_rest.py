"""categories_manage.html + search.html + logs.html 템플릿 렌더 검증.

`create_app` 의 기본 `templates_dir` (= `config.TEMPLATES_DIR`) 를 써서 실제 템플릿
파일이 존재할 때 라우트가 인라인 HTML 대신 템플릿을 렌더하는지 확인한다.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rss_wiki import config, db
from rss_wiki.main import create_app


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
        start_scheduler=False,
    )
    with TestClient(app) as c:
        c.db_path = db_path  # type: ignore[attr-defined]
        yield c


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _insert_feed(db_path: Path, url: str = "https://example.com/feed") -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute("INSERT INTO feeds (url) VALUES (?)", (url,))
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def _insert_category(
    db_path: Path,
    name: str,
    *,
    parent_id: int | None = None,
    is_user_edited: int = 0,
) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO categories (name, parent_id, is_user_edited) VALUES (?, ?, ?)",
            (name, parent_id, is_user_edited),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def _insert_article(
    db_path: Path,
    *,
    feed_id: int,
    url: str,
    title: str,
    primary_category_id: int | None = None,
    llm_summary: str | None = None,
    published_at: str | None = None,
    status: str = "ok",
) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            """
            INSERT INTO articles (
                feed_id, url, title, primary_category_id, llm_summary,
                published_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (feed_id, url, title, primary_category_id, llm_summary, published_at, status),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


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
    conn = _connect(db_path)
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


# ---------- 템플릿 파일 존재 ----------


def test_template_files_exist() -> None:
    assert (config.TEMPLATES_DIR / "categories_manage.html").exists()
    assert (config.TEMPLATES_DIR / "search.html").exists()
    assert (config.TEMPLATES_DIR / "logs.html").exists()


def test_templates_extend_base() -> None:
    for name in ("categories_manage.html", "search.html", "logs.html"):
        text = (config.TEMPLATES_DIR / name).read_text(encoding="utf-8")
        assert '{% extends "base.html" %}' in text, f"{name} must extend base.html"
        assert "{% block content %}" in text, f"{name} must override content block"


# ---------- /categories/manage ----------


def test_manage_page_renders_template_empty(client: TestClient) -> None:
    resp = client.get("/categories/manage")
    assert resp.status_code == 200
    html_text = resp.text
    assert "<title>카테고리 관리 — RSS Wiki</title>" in html_text
    # base.html 의 공통 네비게이션이 함께 렌더된다.
    assert 'href="/feeds"' in html_text
    assert 'href="/search"' in html_text
    assert "등록된 카테고리가 없습니다" in html_text


def test_manage_page_lists_categories_with_forms(client: TestClient) -> None:
    parent = _insert_category(client.db_path, "기술")  # type: ignore[attr-defined]
    _insert_category(client.db_path, "AI", parent_id=parent, is_user_edited=1)  # type: ignore[attr-defined]

    resp = client.get("/categories/manage")
    assert resp.status_code == 200
    html_text = resp.text

    assert "기술" in html_text
    assert "AI" in html_text
    # 두 행 모두 data-category-id 속성이 렌더되어야 한다.
    assert html_text.count('data-category-id="') == 2
    # rename/merge/parent 폼이 각 행에 포함되어야 한다.
    assert "/rename" in html_text
    assert "/merge" in html_text
    assert "/parent" in html_text
    # user_edited 마커
    assert "user" in html_text


# ---------- /search ----------


def test_search_empty_query_renders_template(client: TestClient) -> None:
    resp = client.get("/search")
    assert resp.status_code == 200
    html_text = resp.text
    assert "<title>검색 — RSS Wiki</title>" in html_text
    # 검색 폼
    assert '<form action="/search"' in html_text
    assert 'name="q"' in html_text
    # 빈 쿼리에선 결과 영역이 출력되지 않는다.
    assert "검색 결과 없음" not in html_text


def test_search_renders_results_via_template(client: TestClient) -> None:
    feed_id = _insert_feed(client.db_path)  # type: ignore[attr-defined]
    cat_id = _insert_category(client.db_path, "LLM 에이전트")  # type: ignore[attr-defined]
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/agent",
        title="에이전트 기본기",
        primary_category_id=cat_id,
        llm_summary="LLM 에이전트 소개",
        published_at="2026-04-25",
    )

    resp = client.get("/search", params={"q": "에이전트"})
    assert resp.status_code == 200
    html_text = resp.text

    assert "에이전트 기본기" in html_text
    assert 'href="https://example.com/agent"' in html_text
    assert "LLM 에이전트 소개" in html_text
    assert "2026-04-25" in html_text
    # 카테고리 링크
    assert f'href="/categories/{cat_id}"' in html_text
    # 쿼리가 input value 로 에코된다.
    assert 'value="에이전트"' in html_text
    # data-article-id 속성이 렌더된다.
    assert 'data-article-id="' in html_text


def test_search_no_match_shows_empty_state(client: TestClient) -> None:
    resp = client.get("/search", params={"q": "없는단어xyz"})
    assert resp.status_code == 200
    assert "검색 결과 없음" in resp.text


# ---------- /logs ----------


def test_logs_empty_renders_template(client: TestClient) -> None:
    resp = client.get("/logs")
    assert resp.status_code == 200
    html_text = resp.text
    assert "<title>작업 로그 — RSS Wiki</title>" in html_text
    # 공통 네비게이션
    assert 'href="/feeds"' in html_text
    assert "아직 로그가 없습니다" in html_text
    # 수동 수집 트리거 폼
    assert 'action="/api/fetch"' in html_text


def test_logs_renders_rows_via_template(client: TestClient) -> None:
    _insert_log(
        client.db_path,  # type: ignore[attr-defined]
        job_type="fetch_feed",
        status="ok",
        started_at="2026-04-25T10:00:00",
        finished_at="2026-04-25T10:00:05",
        target_ref="42",
    )
    _insert_log(
        client.db_path,  # type: ignore[attr-defined]
        job_type="summarize",
        status="failed",
        started_at="2026-04-25T10:05:00",
        error_message="LLM timeout exceeded",
        attempt_count=3,
    )

    resp = client.get("/logs")
    assert resp.status_code == 200
    html_text = resp.text

    assert "fetch_feed" in html_text
    assert "summarize" in html_text
    assert "LLM timeout exceeded" in html_text
    assert "42" in html_text
    # 실패 로그는 badge-unread 클래스로 강조된다.
    assert "badge-unread" in html_text
    # 각 로그 행에 data-log-id 속성이 렌더된다.
    assert html_text.count('data-log-id="') == 2
