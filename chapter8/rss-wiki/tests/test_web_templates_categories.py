"""index.html + category.html Jinja2 템플릿 렌더 검증 (TASKS.md §6 템플릿).

`create_app` 의 기본 `templates_dir` (= `config.TEMPLATES_DIR`) 을 그대로 써서
실제 템플릿 파일이 존재할 때 라우트가 인라인 HTML 대신 템플릿을 렌더하는지 확인한다.
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


def _insert_category(
    db_path: Path,
    name: str,
    *,
    parent_id: int | None = None,
    merged_into_id: int | None = None,
    description: str | None = None,
) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO categories (name, parent_id, merged_into_id, description) "
            "VALUES (?, ?, ?, ?)",
            (name, parent_id, merged_into_id, description),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def _upsert_wiki(
    db_path: Path,
    *,
    category_id: int,
    content_markdown: str = "",
    has_unread_updates: int = 0,
) -> None:
    conn = _connect(db_path)
    try:
        conn.execute(
            "INSERT INTO wiki_pages (category_id, content_markdown, has_unread_updates) "
            "VALUES (?, ?, ?)",
            (category_id, content_markdown, has_unread_updates),
        )
        conn.commit()
    finally:
        conn.close()


def _insert_feed(db_path: Path, url: str = "https://example.com/feed") -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute("INSERT INTO feeds (url) VALUES (?)", (url,))
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
    primary_category_id: int,
    llm_summary: str | None = None,
    published_at: str | None = None,
) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            """
            INSERT INTO articles (
                feed_id, url, title, primary_category_id, llm_summary, published_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (feed_id, url, title, primary_category_id, llm_summary, published_at),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def test_template_files_exist() -> None:
    assert (config.TEMPLATES_DIR / "index.html").exists()
    assert (config.TEMPLATES_DIR / "category.html").exists()


def test_index_and_category_templates_extend_base() -> None:
    index = (config.TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")
    category = (config.TEMPLATES_DIR / "category.html").read_text(encoding="utf-8")
    assert '{% extends "base.html" %}' in index
    assert "{% block content %}" in index
    assert '{% extends "base.html" %}' in category
    assert "{% block content %}" in category


def test_index_page_renders_template(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    html_text = resp.text
    # base.html 의 공통 네비게이션이 함께 렌더된다.
    assert 'href="/feeds"' in html_text
    assert 'href="/search"' in html_text
    # 빈 상태 안내 문구
    assert "아직 카테고리가 없습니다" in html_text


def test_index_page_lists_categories_via_template(client: TestClient) -> None:
    root_a = _insert_category(client.db_path, "AI")  # type: ignore[attr-defined]
    root_b = _insert_category(client.db_path, "데이터")  # type: ignore[attr-defined]
    _upsert_wiki(client.db_path, category_id=root_a, has_unread_updates=1)  # type: ignore[attr-defined]

    resp = client.get("/")
    assert resp.status_code == 200
    html_text = resp.text

    assert "AI" in html_text
    assert "데이터" in html_text
    # 두 행 모두 data-category-id 가 템플릿으로 렌더되어야 한다.
    assert html_text.count('data-category-id="') == 2
    assert f'href="/categories/{root_a}"' in html_text
    assert f'href="/categories/{root_b}"' in html_text
    # 읽지 않음 뱃지가 템플릿으로 표시되어야 한다.
    assert "badge-unread" in html_text
    assert "업데이트" in html_text


def test_category_detail_renders_template(client: TestClient) -> None:
    cat = _insert_category(
        client.db_path,  # type: ignore[attr-defined]
        "LLM 에이전트",
        description="LLM 기반 자율 에이전트",
    )
    _upsert_wiki(
        client.db_path,  # type: ignore[attr-defined]
        category_id=cat,
        content_markdown="# LLM 에이전트\n\n## 한줄 요약\n**강조** 요약.",
        has_unread_updates=1,
    )

    resp = client.get(f"/categories/{cat}")
    assert resp.status_code == 200
    html_text = resp.text

    # base.html 의 타이틀 블록이 카테고리명으로 대체되어야 한다.
    assert f"<title>LLM 에이전트 — RSS Wiki</title>" in html_text
    # description 이 렌더된다.
    assert "LLM 기반 자율 에이전트" in html_text
    # 위키 Markdown 이 HTML 로 변환되어야 한다.
    assert "<h1>" in html_text
    assert "<strong>" in html_text
    # 돌아가기 링크
    assert 'href="/"' in html_text


def test_category_detail_renders_articles_and_children(client: TestClient) -> None:
    feed_id = _insert_feed(client.db_path)  # type: ignore[attr-defined]
    parent = _insert_category(client.db_path, "기술")  # type: ignore[attr-defined]
    child = _insert_category(client.db_path, "AI", parent_id=parent)  # type: ignore[attr-defined]
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/a",
        title="첫번째 글",
        primary_category_id=parent,
        llm_summary="요약입니다.",
        published_at="2026-04-25",
    )

    resp = client.get(f"/categories/{parent}")
    assert resp.status_code == 200
    html_text = resp.text

    # 하위 카테고리 섹션
    assert "하위 카테고리" in html_text
    assert f'href="/categories/{child}"' in html_text
    # 원문 리스트
    assert "첫번째 글" in html_text
    assert 'href="https://example.com/a"' in html_text
    assert "요약입니다." in html_text
    assert "2026-04-25" in html_text


def test_category_detail_without_wiki_shows_placeholder(client: TestClient) -> None:
    cat = _insert_category(client.db_path, "Empty")  # type: ignore[attr-defined]
    resp = client.get(f"/categories/{cat}")
    assert resp.status_code == 200
    assert "위키 페이지가 아직 생성되지 않았습니다" in resp.text
