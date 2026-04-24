"""검색 라우트 테스트 (PRD §9, TASKS.md §6).

- GET /search?q=... : SQLite FTS5 MATCH 로 articles 의 title/llm_summary/
  extracted_content 에 대한 키워드 검색.
  · 결과에는 제목, URL, 요약 발췌, 카테고리, 발행일이 표시된다.
  · q 가 비어 있으면 검색 폼만 렌더하고 쿼리를 실행하지 않는다.
  · status='failed' 인 글은 결과에서 제외한다.
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


def _insert_category(db_path: Path, name: str) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
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
    extracted_content: str | None = None,
    published_at: str | None = None,
    status: str = "ok",
) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            """
            INSERT INTO articles (
                feed_id, url, title, primary_category_id, llm_summary,
                extracted_content, published_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feed_id,
                url,
                title,
                primary_category_id,
                llm_summary,
                extracted_content,
                published_at,
                status,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


# ---------- GET /search ----------

def test_search_empty_query_renders_form_only(client: TestClient) -> None:
    resp = client.get("/search")
    assert resp.status_code == 200
    # 검색 폼이 포함된다.
    assert "<form" in resp.text
    assert 'name="q"' in resp.text


def test_search_empty_query_does_not_list_results(client: TestClient) -> None:
    feed_id = _insert_feed(client.db_path)  # type: ignore[attr-defined]
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/a",
        title="파이썬 튜토리얼",
        llm_summary="파이썬을 소개한다.",
    )
    resp = client.get("/search")
    assert resp.status_code == 200
    # q 가 없으면 결과를 출력하지 않는다.
    assert "파이썬 튜토리얼" not in resp.text


def test_search_matches_title(client: TestClient) -> None:
    feed_id = _insert_feed(client.db_path)  # type: ignore[attr-defined]
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/python",
        title="파이썬 튜토리얼",
        llm_summary="언어 소개",
        extracted_content="본문 내용",
    )
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/rust",
        title="러스트 안내",
        llm_summary="시스템 프로그래밍",
        extracted_content="memory safety",
    )

    resp = client.get("/search", params={"q": "파이썬"})
    assert resp.status_code == 200
    assert "파이썬 튜토리얼" in resp.text
    assert "러스트 안내" not in resp.text
    # 원문 링크 노출
    assert "https://example.com/python" in resp.text


def test_search_matches_summary(client: TestClient) -> None:
    feed_id = _insert_feed(client.db_path)  # type: ignore[attr-defined]
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/a",
        title="글 A",
        llm_summary="kubernetes 운영 노하우",
    )
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/b",
        title="글 B",
        llm_summary="프런트엔드 디자인",
    )

    resp = client.get("/search", params={"q": "kubernetes"})
    assert resp.status_code == 200
    assert "글 A" in resp.text
    assert "글 B" not in resp.text


def test_search_matches_extracted_content(client: TestClient) -> None:
    feed_id = _insert_feed(client.db_path)  # type: ignore[attr-defined]
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/a",
        title="글 A",
        extracted_content="transformer 아키텍처 설명",
    )
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/b",
        title="글 B",
        extracted_content="데이터베이스 튜닝",
    )

    resp = client.get("/search", params={"q": "transformer"})
    assert resp.status_code == 200
    assert "글 A" in resp.text
    assert "글 B" not in resp.text


def test_search_excludes_failed_articles(client: TestClient) -> None:
    feed_id = _insert_feed(client.db_path)  # type: ignore[attr-defined]
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/ok",
        title="정상 파이썬 글",
        status="ok",
    )
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/fail",
        title="실패 파이썬 글",
        status="failed",
    )

    resp = client.get("/search", params={"q": "파이썬"})
    assert resp.status_code == 200
    assert "정상 파이썬 글" in resp.text
    assert "실패 파이썬 글" not in resp.text


def test_search_no_match_returns_200_with_empty_state(client: TestClient) -> None:
    feed_id = _insert_feed(client.db_path)  # type: ignore[attr-defined]
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/a",
        title="글 A",
        llm_summary="kubernetes",
    )
    resp = client.get("/search", params={"q": "없는단어xyz"})
    assert resp.status_code == 200
    assert "글 A" not in resp.text


def test_search_includes_category_name(client: TestClient) -> None:
    feed_id = _insert_feed(client.db_path)  # type: ignore[attr-defined]
    cat_id = _insert_category(client.db_path, "LLM 에이전트")  # type: ignore[attr-defined]
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/agent",
        title="에이전트 설계",
        primary_category_id=cat_id,
        llm_summary="agent architecture",
    )
    resp = client.get("/search", params={"q": "agent"})
    assert resp.status_code == 200
    assert "에이전트 설계" in resp.text
    assert "LLM 에이전트" in resp.text


def test_search_whitespace_only_query_treated_as_empty(client: TestClient) -> None:
    feed_id = _insert_feed(client.db_path)  # type: ignore[attr-defined]
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/a",
        title="파이썬 튜토리얼",
        llm_summary="intro",
    )
    resp = client.get("/search", params={"q": "   "})
    assert resp.status_code == 200
    assert "파이썬 튜토리얼" not in resp.text


def test_search_safe_against_fts_special_tokens(client: TestClient) -> None:
    """FTS5 MATCH 는 따옴표/특수문자에 민감하다. 원시 사용자 입력을 그대로 바인딩하면
    `sqlite3.OperationalError: fts5: syntax error` 가 난다. 라우트에서는 안전하게
    이스케이프/쿼리 전환해 500 이 나지 않아야 한다."""
    feed_id = _insert_feed(client.db_path)  # type: ignore[attr-defined]
    _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed_id,
        url="https://example.com/a",
        title="정상 글",
        llm_summary="보통의 요약",
    )
    # 따옴표, AND/OR, 콜론 같은 FTS 연산자가 섞여도 500 이 발생하지 않아야 한다.
    resp = client.get("/search", params={"q": '"unterminated'})
    assert resp.status_code == 200
    resp = client.get("/search", params={"q": "AND OR NOT"})
    assert resp.status_code == 200
    resp = client.get("/search", params={"q": "foo:bar"})
    assert resp.status_code == 200


def test_search_echoes_query_in_form(client: TestClient) -> None:
    resp = client.get("/search", params={"q": "파이썬"})
    assert resp.status_code == 200
    # 검색창에 입력값이 유지되어 있어야 UX 가 자연스럽다.
    assert "파이썬" in resp.text
