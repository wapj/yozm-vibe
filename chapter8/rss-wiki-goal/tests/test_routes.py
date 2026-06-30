"""web/routes.py HTTP 라우트 테스트."""

import pytest


# ── 홈 (카테고리 목록) ────────────────────────────────────────────────────────

def test_index_empty(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "수집된 카테고리가 없습니다" in resp.text


def test_index_with_category(client, app):
    db = app.state.db
    db.execute("INSERT INTO categories(name) VALUES ('AI')")
    db.commit()

    resp = client.get("/")
    assert resp.status_code == 200
    assert "AI" in resp.text


# ── 카테고리 상세 ─────────────────────────────────────────────────────────────

def test_category_detail_not_found(client):
    resp = client.get("/categories/9999")
    assert resp.status_code == 404


def test_category_detail_marks_read(client, app):
    db = app.state.db
    db.execute("INSERT INTO categories(name) VALUES ('AI')")
    db.commit()
    cat_id = db.execute("SELECT id FROM categories WHERE name='AI'").fetchone()["id"]
    db.execute(
        "INSERT INTO wiki_pages(category_id, content_markdown, has_unread_updates) VALUES (?, ?, 1)",
        (cat_id, "# AI"),
    )
    db.commit()

    resp = client.get(f"/categories/{cat_id}")
    assert resp.status_code == 200

    wp = db.execute("SELECT has_unread_updates FROM wiki_pages WHERE category_id=?", (cat_id,)).fetchone()
    assert wp["has_unread_updates"] == 0


# ── 피드 관리 ─────────────────────────────────────────────────────────────────

def test_feeds_list_empty(client):
    resp = client.get("/feeds")
    assert resp.status_code == 200


def test_feeds_add(client, app):
    resp = client.post("/feeds/add", data={"url": "https://example.com/feed"}, follow_redirects=False)
    assert resp.status_code == 303

    db = app.state.db
    row = db.execute("SELECT * FROM feeds WHERE url='https://example.com/feed'").fetchone()
    assert row is not None
    assert row["is_active"] == 1


def test_feeds_add_duplicate_409(client, app):
    db = app.state.db
    db.execute("INSERT INTO feeds(url) VALUES ('https://example.com/feed')")
    db.commit()

    resp = client.post("/feeds/add", data={"url": "https://example.com/feed"})
    assert resp.status_code == 409


def test_feeds_toggle(client, app):
    db = app.state.db
    db.execute("INSERT INTO feeds(url) VALUES ('https://example.com/feed')")
    db.commit()
    feed_id = db.execute("SELECT id FROM feeds").fetchone()["id"]

    resp = client.post(f"/feeds/{feed_id}/toggle", follow_redirects=False)
    assert resp.status_code == 303

    row = db.execute("SELECT is_active FROM feeds WHERE id=?", (feed_id,)).fetchone()
    assert row["is_active"] == 0


def test_feeds_delete(client, app):
    db = app.state.db
    db.execute("INSERT INTO feeds(url) VALUES ('https://example.com/feed')")
    db.commit()
    feed_id = db.execute("SELECT id FROM feeds").fetchone()["id"]

    resp = client.post(f"/feeds/{feed_id}/delete", follow_redirects=False)
    assert resp.status_code == 303

    row = db.execute("SELECT id FROM feeds WHERE id=?", (feed_id,)).fetchone()
    assert row is None


# ── 검색 ──────────────────────────────────────────────────────────────────────

def test_search_empty_query(client):
    resp = client.get("/search")
    assert resp.status_code == 200


def test_search_with_results(client, app):
    db = app.state.db
    db.execute("INSERT INTO feeds(url) VALUES ('https://example.com/feed')")
    db.commit()
    db.execute(
        "INSERT INTO articles(feed_id, url, title, llm_summary) VALUES (1, 'https://example.com/1', 'AI 기술 동향', 'AI 관련 요약')"
    )
    db.commit()

    resp = client.get("/search?q=AI")
    assert resp.status_code == 200
    assert "AI" in resp.text


# ── 로그 ──────────────────────────────────────────────────────────────────────

def test_logs_empty(client):
    resp = client.get("/logs")
    assert resp.status_code == 200


# ── 카테고리 관리 ─────────────────────────────────────────────────────────────

def test_category_manage(client):
    resp = client.get("/categories/manage")
    assert resp.status_code == 200


def test_category_rename(client, app):
    db = app.state.db
    db.execute("INSERT INTO categories(name) VALUES ('AI')")
    db.commit()
    cat_id = db.execute("SELECT id FROM categories WHERE name='AI'").fetchone()["id"]

    resp = client.post(f"/categories/{cat_id}/rename", data={"name": "인공지능"}, follow_redirects=False)
    assert resp.status_code == 303

    row = db.execute("SELECT name, is_user_edited FROM categories WHERE id=?", (cat_id,)).fetchone()
    assert row["name"] == "인공지능"
    assert row["is_user_edited"] == 1


def test_category_set_parent(client, app):
    db = app.state.db
    db.execute("INSERT INTO categories(name) VALUES ('기술')")
    db.execute("INSERT INTO categories(name) VALUES ('AI')")
    db.commit()
    parent_id = db.execute("SELECT id FROM categories WHERE name='기술'").fetchone()["id"]
    child_id = db.execute("SELECT id FROM categories WHERE name='AI'").fetchone()["id"]

    resp = client.post(
        f"/categories/{child_id}/parent",
        data={"parent_id": str(parent_id)},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    row = db.execute("SELECT parent_id FROM categories WHERE id=?", (child_id,)).fetchone()
    assert row["parent_id"] == parent_id
