"""카테고리 라우트 테스트 (PRD §9, TASKS.md §6).

- GET /           : 최상위 카테고리 목록 (parent_id IS NULL, 병합되지 않음)
  · `has_unread_updates=true` 가 목록 상단에 정렬
  · 병합된(merged_into_id) 카테고리와 하위 카테고리는 제외
- GET /categories/{id} : 주제 위키 페이지 + 원문 글 목록
  · Markdown → HTML 렌더
  · 방문 시 wiki_pages.has_unread_updates=0, last_seen_at=datetime('now')
  · 존재하지 않으면 404
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rss_wiki import db
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
        templates_dir=tmp_path / "templates",
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
    merged_into_id: int | None = None,
) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO categories (name, parent_id, merged_into_id) VALUES (?, ?, ?)",
            (name, parent_id, merged_into_id),
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
    last_seen_at: str | None = None,
    last_rebuilt_at: str | None = None,
) -> None:
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO wiki_pages (
                category_id, content_markdown, has_unread_updates,
                last_seen_at, last_rebuilt_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                category_id,
                content_markdown,
                has_unread_updates,
                last_seen_at,
                last_rebuilt_at,
            ),
        )
        conn.commit()
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


def _fetch_wiki(db_path: Path, category_id: int) -> sqlite3.Row | None:
    conn = _connect(db_path)
    try:
        return conn.execute(
            "SELECT * FROM wiki_pages WHERE category_id = ?", (category_id,)
        ).fetchone()
    finally:
        conn.close()


# ---------- GET / ----------

def test_index_returns_200_with_rss_wiki_heading(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert "RSS Wiki" in resp.text


def test_index_lists_top_level_categories_only(client: TestClient) -> None:
    root_a = _insert_category(client.db_path, "AI")  # type: ignore[attr-defined]
    root_b = _insert_category(client.db_path, "데이터")  # type: ignore[attr-defined]
    _insert_category(client.db_path, "LLM", parent_id=root_a)  # type: ignore[attr-defined]

    resp = client.get("/")
    assert resp.status_code == 200
    assert "AI" in resp.text
    assert "데이터" in resp.text
    assert "LLM" not in resp.text  # 하위 카테고리는 목록에서 제외
    # 링크가 실제로 걸려 있어야 함
    assert f"/categories/{root_a}" in resp.text
    assert f"/categories/{root_b}" in resp.text


def test_index_excludes_merged_categories(client: TestClient) -> None:
    keep = _insert_category(client.db_path, "AI")  # type: ignore[attr-defined]
    _insert_category(client.db_path, "인공지능", merged_into_id=keep)  # type: ignore[attr-defined]

    resp = client.get("/")
    assert resp.status_code == 200
    assert "AI" in resp.text
    assert "인공지능" not in resp.text


def test_index_sorts_unread_categories_first(client: TestClient) -> None:
    read_cat = _insert_category(client.db_path, "A-읽음")  # type: ignore[attr-defined]
    unread_cat = _insert_category(client.db_path, "Z-안읽음")  # type: ignore[attr-defined]
    _upsert_wiki(client.db_path, category_id=read_cat, has_unread_updates=0)  # type: ignore[attr-defined]
    _upsert_wiki(client.db_path, category_id=unread_cat, has_unread_updates=1)  # type: ignore[attr-defined]

    resp = client.get("/")
    assert resp.status_code == 200
    # 알파벳 순서라면 A-읽음 이 먼저 나와야 하지만, has_unread 로 Z-안읽음이 위로
    idx_unread = resp.text.find("Z-안읽음")
    idx_read = resp.text.find("A-읽음")
    assert idx_unread != -1 and idx_read != -1
    assert idx_unread < idx_read


def test_index_shows_unread_badge(client: TestClient) -> None:
    cat = _insert_category(client.db_path, "Unread")  # type: ignore[attr-defined]
    _upsert_wiki(client.db_path, category_id=cat, has_unread_updates=1)  # type: ignore[attr-defined]

    resp = client.get("/")
    # 업데이트 뱃지 문구 포함
    assert "업데이트" in resp.text


def test_index_empty_returns_200(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200


# ---------- GET /categories/{id} ----------

def test_category_detail_returns_404_for_unknown(client: TestClient) -> None:
    resp = client.get("/categories/9999")
    assert resp.status_code == 404


def test_category_detail_renders_name(client: TestClient) -> None:
    cat = _insert_category(client.db_path, "LLM 에이전트")  # type: ignore[attr-defined]
    resp = client.get(f"/categories/{cat}")
    assert resp.status_code == 200
    assert "LLM 에이전트" in resp.text


def test_category_detail_renders_wiki_markdown_as_html(client: TestClient) -> None:
    cat = _insert_category(client.db_path, "Topic")  # type: ignore[attr-defined]
    _upsert_wiki(
        client.db_path,  # type: ignore[attr-defined]
        category_id=cat,
        content_markdown="# Topic\n\n## 한줄 요약\n한국어로 작성된 **강조** 요약.",
    )
    resp = client.get(f"/categories/{cat}")
    assert resp.status_code == 200
    # Markdown 이 HTML 로 변환되어 <h1>, <strong> 태그가 등장해야 한다.
    assert "<h1>" in resp.text
    assert "<strong>" in resp.text
    assert "강조" in resp.text


def test_category_detail_without_wiki_page_still_renders(client: TestClient) -> None:
    cat = _insert_category(client.db_path, "Empty")  # type: ignore[attr-defined]
    resp = client.get(f"/categories/{cat}")
    assert resp.status_code == 200
    assert "Empty" in resp.text


def test_category_detail_clears_unread_and_sets_last_seen(client: TestClient) -> None:
    cat = _insert_category(client.db_path, "Topic")  # type: ignore[attr-defined]
    _upsert_wiki(
        client.db_path,  # type: ignore[attr-defined]
        category_id=cat,
        content_markdown="hello",
        has_unread_updates=1,
        last_seen_at=None,
    )
    resp = client.get(f"/categories/{cat}")
    assert resp.status_code == 200
    wiki = _fetch_wiki(client.db_path, cat)  # type: ignore[attr-defined]
    assert wiki is not None
    assert wiki["has_unread_updates"] == 0
    assert wiki["last_seen_at"] is not None


def test_category_detail_lists_articles_in_category(client: TestClient) -> None:
    feed_id = _insert_feed(client.db_path)  # type: ignore[attr-defined]
    cat = _insert_category(client.db_path, "Topic")  # type: ignore[attr-defined]
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/a",
        title="첫번째 글",
        primary_category_id=cat,
        published_at="2026-04-24",
    )
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/b",
        title="두번째 글",
        primary_category_id=cat,
        published_at="2026-04-25",
    )

    resp = client.get(f"/categories/{cat}")
    assert resp.status_code == 200
    assert "첫번째 글" in resp.text
    assert "두번째 글" in resp.text
    assert "https://example.com/a" in resp.text
    assert "https://example.com/b" in resp.text


def test_category_detail_excludes_failed_articles(client: TestClient) -> None:
    feed_id = _insert_feed(client.db_path)  # type: ignore[attr-defined]
    cat = _insert_category(client.db_path, "Topic")  # type: ignore[attr-defined]
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/ok",
        title="정상 글",
        primary_category_id=cat,
        status="ok",
    )
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/fail",
        title="실패 글",
        primary_category_id=cat,
        status="failed",
    )

    resp = client.get(f"/categories/{cat}")
    assert resp.status_code == 200
    assert "정상 글" in resp.text
    assert "실패 글" not in resp.text


def test_category_detail_lists_children(client: TestClient) -> None:
    parent = _insert_category(client.db_path, "기술")  # type: ignore[attr-defined]
    child_a = _insert_category(client.db_path, "AI", parent_id=parent)  # type: ignore[attr-defined]
    _insert_category(client.db_path, "데이터", parent_id=parent)  # type: ignore[attr-defined]

    resp = client.get(f"/categories/{parent}")
    assert resp.status_code == 200
    assert "AI" in resp.text
    assert "데이터" in resp.text
    assert f"/categories/{child_a}" in resp.text


def test_category_detail_children_exclude_merged(client: TestClient) -> None:
    parent = _insert_category(client.db_path, "기술")  # type: ignore[attr-defined]
    target = _insert_category(client.db_path, "AI", parent_id=parent)  # type: ignore[attr-defined]
    _insert_category(  # type: ignore[attr-defined]
        client.db_path,
        "인공지능",
        parent_id=parent,
        merged_into_id=target,
    )

    resp = client.get(f"/categories/{parent}")
    assert resp.status_code == 200
    assert "AI" in resp.text
    assert "인공지능" not in resp.text


def test_category_detail_noop_for_category_without_wiki_row(client: TestClient) -> None:
    cat = _insert_category(client.db_path, "NoWiki")  # type: ignore[attr-defined]
    # wiki_pages 가 없어도 500 이 아니라 200 을 돌려주고, 업데이트문이 0 row 에 대해 동작해야 한다.
    resp = client.get(f"/categories/{cat}")
    assert resp.status_code == 200
    assert _fetch_wiki(client.db_path, cat) is None  # type: ignore[attr-defined]
