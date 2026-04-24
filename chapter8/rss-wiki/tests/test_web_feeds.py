"""피드 라우트 테스트 (PRD §9, TASKS.md §6).

`web/routes.py` 의 GET /feeds, POST /feeds/add, /feeds/{id}/toggle,
/feeds/{id}/delete 동작을 검증한다.
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


def _fetch_feeds(db_path: Path) -> list[sqlite3.Row]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return list(conn.execute("SELECT * FROM feeds ORDER BY id"))
    finally:
        conn.close()


def _fetch_articles(db_path: Path) -> list[sqlite3.Row]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return list(conn.execute("SELECT * FROM articles ORDER BY id"))
    finally:
        conn.close()


def test_get_feeds_empty(client: TestClient) -> None:
    resp = client.get("/feeds")
    assert resp.status_code == 200
    assert "Feeds" in resp.text


def test_post_feeds_add_creates_row(client: TestClient) -> None:
    resp = client.post(
        "/feeds/add",
        data={"url": "https://example.com/feed.xml"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/feeds"

    rows = _fetch_feeds(client.db_path)  # type: ignore[attr-defined]
    assert len(rows) == 1
    assert rows[0]["url"] == "https://example.com/feed.xml"
    assert rows[0]["is_active"] == 1
    assert rows[0]["consecutive_failures"] == 0


def test_post_feeds_add_trims_whitespace(client: TestClient) -> None:
    client.post(
        "/feeds/add",
        data={"url": "  https://example.com/rss  "},
        follow_redirects=False,
    )
    rows = _fetch_feeds(client.db_path)  # type: ignore[attr-defined]
    assert rows[0]["url"] == "https://example.com/rss"


def test_post_feeds_add_duplicate_returns_409(client: TestClient) -> None:
    client.post("/feeds/add", data={"url": "https://example.com/a"}, follow_redirects=False)
    resp = client.post(
        "/feeds/add",
        data={"url": "https://example.com/a"},
        follow_redirects=False,
    )
    assert resp.status_code == 409
    rows = _fetch_feeds(client.db_path)  # type: ignore[attr-defined]
    assert len(rows) == 1


def test_post_feeds_add_empty_url_returns_400(client: TestClient) -> None:
    resp = client.post("/feeds/add", data={"url": "   "}, follow_redirects=False)
    assert resp.status_code == 400
    rows = _fetch_feeds(client.db_path)  # type: ignore[attr-defined]
    assert len(rows) == 0


def test_get_feeds_lists_registered_urls(client: TestClient) -> None:
    client.post("/feeds/add", data={"url": "https://a.example/rss"}, follow_redirects=False)
    client.post("/feeds/add", data={"url": "https://b.example/rss"}, follow_redirects=False)

    resp = client.get("/feeds")
    assert resp.status_code == 200
    assert "https://a.example/rss" in resp.text
    assert "https://b.example/rss" in resp.text


def test_post_feeds_toggle_flips_is_active(client: TestClient) -> None:
    client.post("/feeds/add", data={"url": "https://x.example/rss"}, follow_redirects=False)
    feed_id = _fetch_feeds(client.db_path)[0]["id"]  # type: ignore[attr-defined]

    resp = client.post(f"/feeds/{feed_id}/toggle", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/feeds"
    assert _fetch_feeds(client.db_path)[0]["is_active"] == 0  # type: ignore[attr-defined]

    client.post(f"/feeds/{feed_id}/toggle", follow_redirects=False)
    assert _fetch_feeds(client.db_path)[0]["is_active"] == 1  # type: ignore[attr-defined]


def test_post_feeds_toggle_unknown_returns_404(client: TestClient) -> None:
    resp = client.post("/feeds/9999/toggle", follow_redirects=False)
    assert resp.status_code == 404


def test_post_feeds_delete_removes_row(client: TestClient) -> None:
    client.post("/feeds/add", data={"url": "https://del.example/rss"}, follow_redirects=False)
    feed_id = _fetch_feeds(client.db_path)[0]["id"]  # type: ignore[attr-defined]

    resp = client.post(f"/feeds/{feed_id}/delete", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/feeds"
    assert _fetch_feeds(client.db_path) == []  # type: ignore[attr-defined]


def test_post_feeds_delete_cascades_articles(client: TestClient) -> None:
    client.post("/feeds/add", data={"url": "https://casc.example/rss"}, follow_redirects=False)
    feed_id = _fetch_feeds(client.db_path)[0]["id"]  # type: ignore[attr-defined]

    conn = sqlite3.connect(client.db_path)  # type: ignore[attr-defined]
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        "INSERT INTO articles (feed_id, url, title) VALUES (?, ?, ?)",
        (feed_id, "https://casc.example/post/1", "Hello"),
    )
    conn.commit()
    conn.close()

    assert len(_fetch_articles(client.db_path)) == 1  # type: ignore[attr-defined]

    client.post(f"/feeds/{feed_id}/delete", follow_redirects=False)

    assert _fetch_feeds(client.db_path) == []  # type: ignore[attr-defined]
    assert _fetch_articles(client.db_path) == []  # type: ignore[attr-defined]


def test_post_feeds_delete_unknown_returns_404(client: TestClient) -> None:
    resp = client.post("/feeds/9999/delete", follow_redirects=False)
    assert resp.status_code == 404


def test_post_feeds_add_accepts_optional_title(client: TestClient) -> None:
    resp = client.post(
        "/feeds/add",
        data={"url": "https://t.example/rss", "title": "Title"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    row = _fetch_feeds(client.db_path)[0]  # type: ignore[attr-defined]
    assert row["title"] == "Title"
