"""db.py 스키마 초기화 테스트."""

import sqlite3


def test_tables_created(db):
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    for expected in ("feeds", "categories", "articles", "wiki_pages", "job_logs"):
        assert expected in tables, f"Table {expected} not found"


def test_fts_table_created(db):
    row = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='articles_fts'"
    ).fetchone()
    assert row is not None


def test_indexes_created(db):
    indexes = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()}
    assert "idx_articles_feed" in indexes
    assert "idx_articles_cat" in indexes
    assert "idx_joblogs_started" in indexes


def test_feeds_insert(db):
    db.execute("INSERT INTO feeds(url) VALUES ('https://example.com/feed')")
    db.commit()
    row = db.execute("SELECT * FROM feeds WHERE url='https://example.com/feed'").fetchone()
    assert row is not None
    assert row["is_active"] == 1
    assert row["consecutive_failures"] == 0


def test_fts_trigger_on_article_insert(db):
    db.execute("INSERT INTO feeds(url) VALUES ('https://example.com/feed')")
    db.commit()
    feed_id = db.execute("SELECT id FROM feeds").fetchone()["id"]
    db.execute(
        "INSERT INTO articles(feed_id, url, title, llm_summary) VALUES (?, ?, ?, ?)",
        (feed_id, "https://example.com/1", "테스트 제목", "테스트 요약"),
    )
    db.commit()
    row = db.execute("SELECT * FROM articles_fts WHERE articles_fts MATCH '테스트'").fetchone()
    assert row is not None


def test_wiki_pages_upsert(db):
    db.execute("INSERT INTO categories(name) VALUES ('AI')")
    db.commit()
    cat_id = db.execute("SELECT id FROM categories WHERE name='AI'").fetchone()["id"]
    db.execute(
        "INSERT INTO wiki_pages(category_id, content_markdown) VALUES (?, ?)",
        (cat_id, "# AI\n내용"),
    )
    db.commit()
    row = db.execute("SELECT * FROM wiki_pages WHERE category_id=?", (cat_id,)).fetchone()
    assert row["content_markdown"] == "# AI\n내용"
    assert row["has_unread_updates"] == 0
