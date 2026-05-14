from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from rss_wiki.storage.db import init_db
from rss_wiki.storage.repo import (
    get_feed_by_id,
    insert_article,
    insert_magazine,
    link_article_category,
    list_feeds,
    record_feed_failure,
    set_feed_enabled,
    upsert_category,
    upsert_feed,
    upsert_tag,
)
from rss_wiki.web.app import create_app
from rss_wiki.web.markdown import render_markdown


def test_healthz_returns_ok(tmp_path):
    client = TestClient(create_app(tmp_path / "x.db"))
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_index_returns_200(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "RSS Wiki" in response.text


def test_create_app_runs_init_db_and_enables_wal(tmp_path):
    tmp_db = tmp_path / "x.db"
    with TestClient(create_app(tmp_db)) as client:
        client.get("/healthz")
    assert tmp_db.exists()
    conn = sqlite3.connect(tmp_db)
    try:
        result = conn.execute("PRAGMA journal_mode").fetchone()
        assert result[0] == "wal"
    finally:
        conn.close()


def test_render_markdown_basic():
    result = render_markdown("# Hello")
    assert "<h1>" in result
    assert "Hello" in result

    result2 = render_markdown("[link](https://example.com)")
    assert "<a" in result2
    assert "https://example.com" in result2


def test_magazines_list_empty(tmp_path):
    tmp_db = tmp_path / "x.db"
    with TestClient(create_app(tmp_db)) as client:
        response = client.get("/magazines")
    assert response.status_code == 200
    assert "매거진 인덱스" in response.text
    assert "아직 항목이 없습니다" in response.text


def test_magazines_list_with_entries(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        insert_magazine(conn, kind="daily", published_at="2026-05-04", file_path="/tmp/dummy1.md")
        insert_magazine(conn, kind="weekly", published_at="2026-05-03", file_path="/tmp/dummy2.md")
        conn.commit()
    finally:
        conn.close()

    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        response = client.get("/magazines")
    assert response.status_code == 200
    assert "2026-05-04" in response.text
    assert "2026-05-03" in response.text
    assert "daily" in response.text
    assert "weekly" in response.text


def test_magazine_detail_renders_markdown(tmp_path):
    tmp_db = tmp_path / "x.db"
    md_path = tmp_path / "out.md"
    md_path.write_text("# Hello\n\n본문 텍스트", encoding="utf-8")

    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        mag_id = insert_magazine(conn, kind="daily", published_at="2026-05-05", file_path=str(md_path))
        conn.commit()
    finally:
        conn.close()

    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        response = client.get(f"/magazines/{mag_id}")
    assert response.status_code == 200
    assert "<h1>" in response.text
    assert "Hello" in response.text
    assert "본문 텍스트" in response.text
    assert "daily 2026-05-05" in response.text


def test_magazine_detail_404_for_missing_id(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        response = client.get("/magazines/99999")
    assert response.status_code == 404


def test_magazine_detail_404_when_file_missing(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        mag_id = insert_magazine(
            conn, kind="daily", published_at="2026-05-05", file_path="/nonexistent/path.md"
        )
        conn.commit()
    finally:
        conn.close()

    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        response = client.get(f"/magazines/{mag_id}")
    assert response.status_code == 404


def test_categories_index_empty(tmp_path):
    tmp_db = tmp_path / "x.db"
    with TestClient(create_app(tmp_db)) as client:
        response = client.get("/categories")
    assert response.status_code == 200
    assert "카테고리" in response.text
    assert "아직 항목이 없습니다" in response.text


def test_categories_index_with_entries(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        upsert_category(conn, "AI")
        upsert_category(conn, "데이터")
        conn.commit()
    finally:
        conn.close()

    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        response = client.get("/categories")
    assert response.status_code == 200
    assert "ai" in response.text
    assert "데이터" in response.text
    assert 'href="/categories/ai"' in response.text


def test_category_articles_renders_articles(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed_id = upsert_feed(conn, name="테스트피드", url="https://example.com/feed")
        cat_id = upsert_category(conn, "AI")
        art_id1 = insert_article(
            conn,
            feed_id=feed_id,
            url="https://example.com/a1",
            url_hash="h1",
            title="글 제목 1",
            title_hash="t1",
            published_at="2026-05-01",
            content=None,
            summary=None,
        )
        art_id2 = insert_article(
            conn,
            feed_id=feed_id,
            url="https://example.com/a2",
            url_hash="h2",
            title="글 제목 2",
            title_hash="t2",
            published_at="2026-05-02",
            content=None,
            summary=None,
        )
        link_article_category(conn, art_id1, cat_id)
        link_article_category(conn, art_id2, cat_id)
        conn.commit()
    finally:
        conn.close()

    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        response = client.get("/categories/AI")
    assert response.status_code == 200
    assert "글 제목 1" in response.text
    assert "글 제목 2" in response.text
    assert "카테고리: ai" in response.text


def test_category_articles_404_for_missing_name(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        response = client.get("/categories/존재하지않는카테고리")
    assert response.status_code == 404


def test_tag_articles_404_for_missing_name(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        response = client.get("/tags/없는태그")
    assert response.status_code == 404


def test_feeds_index_empty(tmp_path):
    tmp_db = tmp_path / "x.db"
    with TestClient(create_app(tmp_db)) as client:
        response = client.get("/feeds")
    assert response.status_code == 200
    assert "피드" in response.text
    assert "아직 등록된 피드가 없습니다" in response.text


def test_feeds_index_with_entries(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        upsert_feed(conn, "Google News", "https://news.google.com/rss")
        upsert_feed(conn, "HN", "https://news.ycombinator.com/rss")
        conn.commit()
    finally:
        conn.close()

    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        response = client.get("/feeds")
    assert response.status_code == 200
    assert "Google News" in response.text
    assert "https://news.google.com/rss" in response.text
    assert "HN" in response.text
    assert 'href="/feeds/' in response.text


def test_feed_edit_form_renders(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed_id = upsert_feed(conn, "Google News", "https://news.google.com/rss")
        set_feed_enabled(conn, feed_id, False)
        conn.commit()
    finally:
        conn.close()

    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        response = client.get(f"/feeds/{feed_id}/edit")
    assert response.status_code == 200
    assert "Google News" in response.text
    assert "https://news.google.com/rss" in response.text
    assert 'action="/feeds/' in response.text


def test_feed_edit_404_for_missing_id(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        response = client.get("/feeds/99999/edit")
    assert response.status_code == 404


def test_post_feeds_creates(tmp_path):
    tmp_db = tmp_path / "x.db"
    with TestClient(create_app(tmp_db)) as client:
        response = client.post(
            "/feeds",
            data={"url": "https://example.com/rss", "name": "Example"},
            follow_redirects=False,
        )
    assert response.status_code == 303
    assert response.headers["location"] == "/feeds?ok=created"
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feeds = list_feeds(conn)
    finally:
        conn.close()
    assert len(feeds) == 1
    assert feeds[0]["url"] == "https://example.com/rss"
    assert feeds[0]["name"] == "Example"


def test_post_feeds_normalizes_url(tmp_path):
    tmp_db = tmp_path / "x.db"
    with TestClient(create_app(tmp_db)) as client:
        response = client.post(
            "/feeds",
            data={"url": "https://example.com/rss?utm_source=x", "name": "Example"},
            follow_redirects=False,
        )
    assert response.status_code == 303
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feeds = list_feeds(conn)
    finally:
        conn.close()
    assert len(feeds) == 1
    assert "utm_source" not in feeds[0]["url"]


def test_post_feeds_duplicate_url_idempotent(tmp_path):
    tmp_db = tmp_path / "x.db"
    with TestClient(create_app(tmp_db)) as client:
        r1 = client.post(
            "/feeds",
            data={"url": "https://example.com/rss", "name": "A"},
            follow_redirects=False,
        )
        r2 = client.post(
            "/feeds",
            data={"url": "https://example.com/rss", "name": "B"},
            follow_redirects=False,
        )
    assert r1.status_code == 303
    assert r2.status_code == 303
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feeds = list_feeds(conn)
    finally:
        conn.close()
    assert len(feeds) == 1


def test_post_feeds_rejects_empty_url(tmp_path):
    tmp_db = tmp_path / "x.db"
    with TestClient(create_app(tmp_db)) as client:
        response = client.post(
            "/feeds",
            data={"url": " ", "name": "x"},
            follow_redirects=False,
        )
    assert response.status_code == 400


def test_post_feed_update(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed_id = upsert_feed(conn, "Old", "https://example.com/rss")
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        response = client.post(
            f"/feeds/{feed_id}",
            data={"name": "New", "enabled": "on"},
            follow_redirects=False,
        )
    assert response.status_code == 303
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed = get_feed_by_id(conn, feed_id)
    finally:
        conn.close()
    assert feed["name"] == "New"
    assert feed["enabled"] == 1


def test_post_feed_update_disables_when_unchecked(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed_id = upsert_feed(conn, "Old", "https://example.com/rss")
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        response = client.post(
            f"/feeds/{feed_id}",
            data={"name": "Same"},
            follow_redirects=False,
        )
    assert response.status_code == 303
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed = get_feed_by_id(conn, feed_id)
    finally:
        conn.close()
    assert feed["enabled"] == 0


def test_post_feed_delete(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed_id = upsert_feed(conn, "Test", "https://example.com/rss")
        art_id = insert_article(
            conn,
            feed_id=feed_id,
            url="https://example.com/a1",
            url_hash="h1",
            title="Article 1",
            title_hash="t1",
            published_at="2026-05-01",
            content=None,
            summary=None,
        )
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        response = client.post(f"/feeds/{feed_id}/delete", follow_redirects=False)
    assert response.status_code == 303
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feeds = list_feeds(conn)
        article = conn.execute("SELECT * FROM articles WHERE id = ?", (art_id,)).fetchone()
    finally:
        conn.close()
    assert len(feeds) == 0
    assert article is not None
    assert article["feed_id"] is None
    assert article["feed_url_snapshot"] is not None


def test_post_feed_toggle(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed_id = upsert_feed(conn, "Test", "https://example.com/rss")
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        r1 = client.post(f"/feeds/{feed_id}/toggle", follow_redirects=False)
        assert r1.status_code == 303
        conn2 = sqlite3.connect(tmp_db)
        conn2.row_factory = sqlite3.Row
        try:
            feed = get_feed_by_id(conn2, feed_id)
            assert feed["enabled"] == 0
        finally:
            conn2.close()
        r2 = client.post(f"/feeds/{feed_id}/toggle", follow_redirects=False)
        assert r2.status_code == 303
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed = get_feed_by_id(conn, feed_id)
    finally:
        conn.close()
    assert feed["enabled"] == 1


def test_post_feed_reset(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed_id = upsert_feed(conn, "Test", "https://example.com/rss")
        record_feed_failure(conn, feed_id)
        record_feed_failure(conn, feed_id)
        record_feed_failure(conn, feed_id)
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        response = client.post(f"/feeds/{feed_id}/reset", follow_redirects=False)
    assert response.status_code == 303
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed = get_feed_by_id(conn, feed_id)
    finally:
        conn.close()
    assert feed["consecutive_failures"] == 0


def test_post_feed_404_for_missing_id(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        response = client.post("/feeds/99999/delete", follow_redirects=False)
    assert response.status_code == 404


def test_static_style_css_served(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        resp = client.get("/static/style.css")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/css")
    body = resp.text
    assert ":root" in body
    assert "--color-bg" in body
    assert "@media (prefers-color-scheme: dark)" in body
    assert ".gnb" in body


def test_base_html_includes_stylesheet_link(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert '<link rel="stylesheet" href="/static/style.css">' in resp.text


def test_base_html_renders_gnb_with_four_links(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert 'class="gnb"' in resp.text
    assert "매거진" in resp.text
    assert "카테고리" in resp.text
    assert "태그" in resp.text
    assert "피드 관리" in resp.text
    assert 'href="/magazines"' in resp.text
    assert 'href="/categories"' in resp.text
    assert 'href="/tags"' in resp.text
    assert 'href="/feeds"' in resp.text


def test_base_html_includes_viewport_meta(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert '<meta name="viewport"' in resp.text


def test_get_feeds_new_returns_form(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        resp = client.get("/feeds/new")
    assert resp.status_code == 200
    assert '<form method="post" action="/feeds">' in resp.text
    assert 'name="url"' in resp.text
    assert 'name="name"' in resp.text


def test_post_feed_update_changes_url(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed_id = upsert_feed(conn, "X", "https://a.example.com/rss")
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        response = client.post(
            f"/feeds/{feed_id}",
            data={"name": "X", "url": "https://b.example.com/rss", "enabled": "on"},
            follow_redirects=False,
        )
    assert response.status_code == 303
    assert response.headers["location"] == "/feeds?ok=updated"
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed = get_feed_by_id(conn, feed_id)
    finally:
        conn.close()
    assert feed["url"] == "https://b.example.com/rss"


def test_post_feed_update_duplicate_url_redirects_to_edit_with_error(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed_a_id = upsert_feed(conn, "A", "https://a.example.com/rss")
        feed_b_id = upsert_feed(conn, "B", "https://b.example.com/rss")
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        response = client.post(
            f"/feeds/{feed_b_id}",
            data={"name": "B", "url": "https://a.example.com/rss"},
            follow_redirects=False,
        )
    assert response.status_code == 303
    assert response.headers["location"] == f"/feeds/{feed_b_id}/edit?error=duplicate"
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed_b = get_feed_by_id(conn, feed_b_id)
    finally:
        conn.close()
    assert feed_b["url"] == "https://b.example.com/rss"


def test_post_feed_update_empty_url_keeps_existing(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed_id = upsert_feed(conn, "X", "https://example.com/rss")
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        response = client.post(
            f"/feeds/{feed_id}",
            data={"name": "X", "url": ""},
            follow_redirects=False,
        )
    assert response.status_code == 303
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed = get_feed_by_id(conn, feed_id)
    finally:
        conn.close()
    assert feed["url"] == "https://example.com/rss"


def test_feeds_create_redirects_with_ok(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        response = client.post(
            "/feeds",
            data={"url": "https://example.com/rss"},
            follow_redirects=False,
        )
    assert response.status_code == 303
    assert response.headers["location"] == "/feeds?ok=created"


def test_feeds_index_renders_flash_on_ok_query(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        resp = client.get("/feeds?ok=created")
    assert resp.status_code == 200
    assert 'class="flash flash-success"' in resp.text
    assert "피드를 추가했습니다." in resp.text


def test_feed_edit_renders_flash_on_error_query(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        feed_id = upsert_feed(conn, "X", "https://example.com/rss")
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        resp = client.get(f"/feeds/{feed_id}/edit?error=duplicate")
    assert resp.status_code == 200
    assert 'class="flash flash-danger"' in resp.text


# ── T-019C: 7 new test cases ─────────────────────────────────────────────


def test_tags_index_empty(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        resp = client.get("/tags")
    assert resp.status_code == 200
    assert "태그" in resp.text
    assert "아직 항목이 없습니다" in resp.text


def test_tags_index_with_entries(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        upsert_tag(conn, "ai")
        upsert_tag(conn, "kotlin")
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        resp = client.get("/tags")
    assert resp.status_code == 200
    assert "ai" in resp.text
    assert "kotlin" in resp.text
    assert 'href="/tags/ai"' in resp.text
    assert 'href="/tags/kotlin"' in resp.text
    assert 'class="card"' in resp.text


def test_active_nav_marks_feeds_link_when_on_feeds_page(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        resp = client.get("/feeds")
    assert resp.status_code == 200
    assert 'href="/feeds" class="active"' in resp.text


def test_active_nav_marks_magazines_link_when_on_magazines_page(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        resp = client.get("/magazines")
    assert resp.status_code == 200
    assert 'href="/magazines" class="active"' in resp.text


def test_active_nav_marks_tags_link_when_on_tags_page(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        resp = client.get("/tags")
    assert resp.status_code == 200
    assert 'href="/tags" class="active"' in resp.text


def test_feeds_html_uses_btn_class(tmp_path):
    tmp_db = tmp_path / "x.db"
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    try:
        upsert_feed(conn, "Example", "https://example.com/rss")
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(tmp_db, run_init_db=False)) as client:
        resp = client.get("/feeds")
    assert resp.status_code == 200
    assert 'class="btn' in resp.text


def test_magazine_body_styles_in_css(tmp_path):
    with TestClient(create_app(tmp_path / "x.db")) as client:
        resp = client.get("/static/style.css")
    assert resp.status_code == 200
    assert ".magazine-body" in resp.text
    assert "pre" in resp.text
    assert "blockquote" in resp.text
