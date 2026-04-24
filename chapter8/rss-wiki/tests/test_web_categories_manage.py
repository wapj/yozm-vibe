"""카테고리 관리 라우트 테스트 (PRD §8.3, §9).

- GET  /categories/manage       : 전체 카테고리 테이블 렌더
- POST /categories/{id}/rename  : 이름 수정, `is_user_edited=1`
- POST /categories/{id}/merge   : 소스 → 타겟 병합.
    · 속한 articles.primary_category_id 를 타겟으로 이동
    · 소스의 wiki_pages 삭제
    · 소스 categories.merged_into_id = 타겟
    · 타겟 wiki_pages.has_unread_updates = 1 (rebuild 트리거용 마커)
- POST /categories/{id}/parent  : 상위 카테고리 지정/해제.
    · 2단계 고정 (부모의 부모는 없음)
    · 자기 자신을 부모로 지정 불가
    · 하위 카테고리를 가진 노드를 누군가의 하위로 붙일 수 없음 (3단계 방지)
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
    is_user_edited: int = 0,
) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO categories (name, parent_id, merged_into_id, is_user_edited) "
            "VALUES (?, ?, ?, ?)",
            (name, parent_id, merged_into_id, is_user_edited),
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


def _insert_article(
    db_path: Path,
    *,
    feed_id: int,
    url: str,
    title: str,
    primary_category_id: int | None = None,
) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO articles (feed_id, url, title, primary_category_id) "
            "VALUES (?, ?, ?, ?)",
            (feed_id, url, title, primary_category_id),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def _fetch_category(db_path: Path, category_id: int) -> sqlite3.Row | None:
    conn = _connect(db_path)
    try:
        return conn.execute(
            "SELECT * FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
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


# ---------- GET /categories/manage ----------

def test_manage_returns_200_even_when_empty(client: TestClient) -> None:
    resp = client.get("/categories/manage")
    assert resp.status_code == 200


def test_manage_lists_all_categories_including_children(client: TestClient) -> None:
    parent = _insert_category(client.db_path, "기술")  # type: ignore[attr-defined]
    _insert_category(client.db_path, "AI", parent_id=parent)  # type: ignore[attr-defined]
    _insert_category(client.db_path, "데이터")  # type: ignore[attr-defined]

    resp = client.get("/categories/manage")
    assert resp.status_code == 200
    assert "기술" in resp.text
    assert "AI" in resp.text
    assert "데이터" in resp.text


def test_manage_excludes_merged_categories(client: TestClient) -> None:
    keep = _insert_category(client.db_path, "AI")  # type: ignore[attr-defined]
    _insert_category(client.db_path, "인공지능", merged_into_id=keep)  # type: ignore[attr-defined]

    resp = client.get("/categories/manage")
    assert resp.status_code == 200
    assert "AI" in resp.text
    assert "인공지능" not in resp.text


# ---------- POST /categories/{id}/rename ----------

def test_rename_updates_name_and_sets_user_edited(client: TestClient) -> None:
    cat = _insert_category(client.db_path, "원래이름")  # type: ignore[attr-defined]

    resp = client.post(
        f"/categories/{cat}/rename",
        data={"name": "새이름"},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    row = _fetch_category(client.db_path, cat)  # type: ignore[attr-defined]
    assert row is not None
    assert row["name"] == "새이름"
    assert row["is_user_edited"] == 1


def test_rename_strips_whitespace(client: TestClient) -> None:
    cat = _insert_category(client.db_path, "x")  # type: ignore[attr-defined]
    resp = client.post(
        f"/categories/{cat}/rename",
        data={"name": "  공백제거  "},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    row = _fetch_category(client.db_path, cat)  # type: ignore[attr-defined]
    assert row is not None
    assert row["name"] == "공백제거"


def test_rename_rejects_empty_name(client: TestClient) -> None:
    cat = _insert_category(client.db_path, "원래이름")  # type: ignore[attr-defined]
    resp = client.post(
        f"/categories/{cat}/rename",
        data={"name": "   "},
        follow_redirects=False,
    )
    assert resp.status_code == 400
    row = _fetch_category(client.db_path, cat)  # type: ignore[attr-defined]
    assert row is not None
    assert row["name"] == "원래이름"


def test_rename_duplicate_returns_409(client: TestClient) -> None:
    a = _insert_category(client.db_path, "A")  # type: ignore[attr-defined]
    _insert_category(client.db_path, "B")  # type: ignore[attr-defined]
    resp = client.post(
        f"/categories/{a}/rename",
        data={"name": "B"},
        follow_redirects=False,
    )
    assert resp.status_code == 409


def test_rename_unknown_id_returns_404(client: TestClient) -> None:
    resp = client.post(
        "/categories/9999/rename",
        data={"name": "x"},
        follow_redirects=False,
    )
    assert resp.status_code == 404


# ---------- POST /categories/{id}/merge ----------

def test_merge_moves_articles_and_marks_target_unread(client: TestClient) -> None:
    feed = _insert_feed(client.db_path)  # type: ignore[attr-defined]
    source = _insert_category(client.db_path, "인공지능")  # type: ignore[attr-defined]
    target = _insert_category(client.db_path, "AI")  # type: ignore[attr-defined]
    _upsert_wiki(client.db_path, category_id=source, content_markdown="src wiki")  # type: ignore[attr-defined]
    _upsert_wiki(client.db_path, category_id=target, content_markdown="tgt wiki")  # type: ignore[attr-defined]
    a1 = _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed,
        url="https://example.com/a",
        title="a",
        primary_category_id=source,
    )
    a2 = _insert_article(
        client.db_path,  # type: ignore[attr-defined]
        feed_id=feed,
        url="https://example.com/b",
        title="b",
        primary_category_id=source,
    )

    resp = client.post(
        f"/categories/{source}/merge",
        data={"target_id": str(target)},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    src_row = _fetch_category(client.db_path, source)  # type: ignore[attr-defined]
    assert src_row is not None
    assert src_row["merged_into_id"] == target

    # 소스 wiki_pages 는 사라진다.
    assert _fetch_wiki(client.db_path, source) is None  # type: ignore[attr-defined]

    # 타겟 wiki_pages 는 남아 있고 unread 플래그가 올라간다 (rebuild 마커).
    tgt_wiki = _fetch_wiki(client.db_path, target)  # type: ignore[attr-defined]
    assert tgt_wiki is not None
    assert tgt_wiki["has_unread_updates"] == 1

    # articles 가 타겟 카테고리로 이동.
    conn = _connect(client.db_path)  # type: ignore[attr-defined]
    try:
        for art_id in (a1, a2):
            row = conn.execute(
                "SELECT primary_category_id FROM articles WHERE id = ?", (art_id,)
            ).fetchone()
            assert row is not None
            assert row["primary_category_id"] == target
    finally:
        conn.close()


def test_merge_creates_target_wiki_marker_when_none_exists(client: TestClient) -> None:
    source = _insert_category(client.db_path, "인공지능")  # type: ignore[attr-defined]
    target = _insert_category(client.db_path, "AI")  # type: ignore[attr-defined]

    resp = client.post(
        f"/categories/{source}/merge",
        data={"target_id": str(target)},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    # 타겟 wiki_pages 가 없었더라도 rebuild 트리거 마커 행이 만들어진다.
    tgt_wiki = _fetch_wiki(client.db_path, target)  # type: ignore[attr-defined]
    assert tgt_wiki is not None
    assert tgt_wiki["has_unread_updates"] == 1


def test_merge_into_self_returns_400(client: TestClient) -> None:
    cat = _insert_category(client.db_path, "x")  # type: ignore[attr-defined]
    resp = client.post(
        f"/categories/{cat}/merge",
        data={"target_id": str(cat)},
        follow_redirects=False,
    )
    assert resp.status_code == 400


def test_merge_unknown_source_returns_404(client: TestClient) -> None:
    target = _insert_category(client.db_path, "AI")  # type: ignore[attr-defined]
    resp = client.post(
        "/categories/9999/merge",
        data={"target_id": str(target)},
        follow_redirects=False,
    )
    assert resp.status_code == 404


def test_merge_unknown_target_returns_400(client: TestClient) -> None:
    source = _insert_category(client.db_path, "AI")  # type: ignore[attr-defined]
    resp = client.post(
        f"/categories/{source}/merge",
        data={"target_id": "9999"},
        follow_redirects=False,
    )
    assert resp.status_code == 400


# ---------- POST /categories/{id}/parent ----------

def test_parent_sets_parent_id(client: TestClient) -> None:
    parent = _insert_category(client.db_path, "기술")  # type: ignore[attr-defined]
    child = _insert_category(client.db_path, "AI")  # type: ignore[attr-defined]

    resp = client.post(
        f"/categories/{child}/parent",
        data={"parent_id": str(parent)},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    row = _fetch_category(client.db_path, child)  # type: ignore[attr-defined]
    assert row is not None
    assert row["parent_id"] == parent


def test_parent_empty_clears_parent(client: TestClient) -> None:
    parent = _insert_category(client.db_path, "기술")  # type: ignore[attr-defined]
    child = _insert_category(client.db_path, "AI", parent_id=parent)  # type: ignore[attr-defined]

    resp = client.post(
        f"/categories/{child}/parent",
        data={"parent_id": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    row = _fetch_category(client.db_path, child)  # type: ignore[attr-defined]
    assert row is not None
    assert row["parent_id"] is None


def test_parent_self_returns_400(client: TestClient) -> None:
    cat = _insert_category(client.db_path, "x")  # type: ignore[attr-defined]
    resp = client.post(
        f"/categories/{cat}/parent",
        data={"parent_id": str(cat)},
        follow_redirects=False,
    )
    assert resp.status_code == 400


def test_parent_enforces_two_level_depth(client: TestClient) -> None:
    # 기술 - AI 구조에서 "LLM" 을 AI 밑에 넣으려 하면 3단계가 되므로 400
    tech = _insert_category(client.db_path, "기술")  # type: ignore[attr-defined]
    ai = _insert_category(client.db_path, "AI", parent_id=tech)  # type: ignore[attr-defined]
    llm = _insert_category(client.db_path, "LLM")  # type: ignore[attr-defined]

    resp = client.post(
        f"/categories/{llm}/parent",
        data={"parent_id": str(ai)},
        follow_redirects=False,
    )
    assert resp.status_code == 400
    row = _fetch_category(client.db_path, llm)  # type: ignore[attr-defined]
    assert row is not None
    assert row["parent_id"] is None


def test_parent_rejects_moving_node_that_has_children(client: TestClient) -> None:
    # "AI" 가 자신의 자식("LLM") 을 가지고 있는 상태에서 AI 를 "기술" 의 자식으로 붙이면
    # "기술 -> AI -> LLM" 이 되어 3단계가 되므로 거부.
    tech = _insert_category(client.db_path, "기술")  # type: ignore[attr-defined]
    ai = _insert_category(client.db_path, "AI")  # type: ignore[attr-defined]
    _insert_category(client.db_path, "LLM", parent_id=ai)  # type: ignore[attr-defined]

    resp = client.post(
        f"/categories/{ai}/parent",
        data={"parent_id": str(tech)},
        follow_redirects=False,
    )
    assert resp.status_code == 400


def test_parent_unknown_id_returns_404(client: TestClient) -> None:
    resp = client.post(
        "/categories/9999/parent",
        data={"parent_id": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 404


def test_parent_unknown_target_returns_400(client: TestClient) -> None:
    cat = _insert_category(client.db_path, "x")  # type: ignore[attr-defined]
    resp = client.post(
        f"/categories/{cat}/parent",
        data={"parent_id": "9999"},
        follow_redirects=False,
    )
    assert resp.status_code == 400
