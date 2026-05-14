import sqlite3
import pytest
from rss_wiki.storage.db import get_connection, init_db
from rss_wiki.storage.repo import (
    upsert_feed,
    get_feed_by_url,
    insert_article,
    get_article_by_url_hash,
    get_article_by_title_hash,
    upsert_category,
    upsert_tag,
    link_article_category,
    link_article_tag,
    insert_magazine,
    link_magazine_article,
    record_feed_success,
    record_feed_failure,
    list_failing_feeds,
    list_categories,
    list_articles_by_ids,
    update_article_summary,
    list_categories_for_article,
    list_tags_for_article,
    list_tags,
    list_articles_by_category,
    list_articles_by_tag,
    list_articles_published_between,
    list_unanalyzed_article_ids,
    list_feeds,
    update_feed,
    set_feed_enabled,
    reset_feed_failures,
    delete_feed,
)


@pytest.fixture
def conn(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    c = get_connection(db_path)
    yield c
    c.close()


def _insert_test_article(conn, feed_id, url_hash="hash_url_1", title_hash="hash_title_1"):
    return insert_article(
        conn,
        feed_id=feed_id,
        url="https://example.com/article",
        url_hash=url_hash,
        title="Test Article",
        title_hash=title_hash,
        published_at="2026-05-05T00:00:00",
        content="Some content",
        summary="Some summary",
    )


# (a) upsert_feed 같은 url 두 번 호출 — 동일 feed_id, 예외 없음
def test_upsert_feed_idempotent(conn):
    id1 = upsert_feed(conn, "Feed A", "https://feed.example.com/rss")
    id2 = upsert_feed(conn, "Feed A", "https://feed.example.com/rss")
    assert isinstance(id1, int)
    assert id1 == id2


# (b) get_feed_by_url — 존재 시 Row, 미존재 시 None
def test_get_feed_by_url(conn):
    upsert_feed(conn, "Feed B", "https://b.example.com/rss")
    row = get_feed_by_url(conn, "https://b.example.com/rss")
    assert row is not None
    assert row["name"] == "Feed B"
    assert row["url"] == "https://b.example.com/rss"

    missing = get_feed_by_url(conn, "https://nonexistent.example.com/rss")
    assert missing is None


# (c) insert_article 정상 흐름 — 반환값 정수, articles 테이블 1건 적재
def test_insert_article_normal(conn):
    feed_id = upsert_feed(conn, "Feed C", "https://c.example.com/rss")
    article_id = _insert_test_article(conn, feed_id)
    assert isinstance(article_id, int)
    count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    assert count == 1


# (d) insert_article 중복 — 동일 url_hash 두 번째 호출 시 IntegrityError
def test_insert_article_duplicate_raises(conn):
    feed_id = upsert_feed(conn, "Feed D", "https://d.example.com/rss")
    _insert_test_article(conn, feed_id, url_hash="dup_hash")
    with pytest.raises(sqlite3.IntegrityError):
        _insert_test_article(conn, feed_id, url_hash="dup_hash")


# (e) get_article_by_url_hash — 조회 가능, 미존재 시 None
def test_get_article_by_url_hash(conn):
    feed_id = upsert_feed(conn, "Feed E", "https://e.example.com/rss")
    _insert_test_article(conn, feed_id, url_hash="url_hash_e")
    row = get_article_by_url_hash(conn, "url_hash_e")
    assert row is not None
    assert row["url_hash"] == "url_hash_e"

    assert get_article_by_url_hash(conn, "nonexistent") is None


# (f) get_article_by_title_hash — 조회 가능, 미존재 시 None
def test_get_article_by_title_hash(conn):
    feed_id = upsert_feed(conn, "Feed F", "https://f.example.com/rss")
    _insert_test_article(conn, feed_id, title_hash="title_hash_f")
    row = get_article_by_title_hash(conn, "title_hash_f")
    assert row is not None
    assert row["title_hash"] == "title_hash_f"

    assert get_article_by_title_hash(conn, "nonexistent") is None


# (g) upsert_category 멱등 + 정규화 — "Python", "  python  ", "PYTHON" 모두 동일 id
def test_upsert_category_idempotent_normalized(conn):
    id1 = upsert_category(conn, "Python")
    id2 = upsert_category(conn, "  python  ")
    id3 = upsert_category(conn, "PYTHON")
    assert isinstance(id1, int)
    assert id1 == id2 == id3
    count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    assert count == 1


# (h) upsert_tag 멱등 + 정규화 — 동일 패턴
def test_upsert_tag_idempotent_normalized(conn):
    id1 = upsert_tag(conn, "AI")
    id2 = upsert_tag(conn, "  ai  ")
    id3 = upsert_tag(conn, "Ai")
    assert isinstance(id1, int)
    assert id1 == id2 == id3
    count = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    assert count == 1


# (i) link_article_category 멱등 — 동일 페어 두 번 호출 후 1행만 존재
def test_link_article_category_idempotent(conn):
    feed_id = upsert_feed(conn, "Feed G", "https://g.example.com/rss")
    article_id = _insert_test_article(conn, feed_id, url_hash="hash_g", title_hash="th_g")
    category_id = upsert_category(conn, "tech")
    link_article_category(conn, article_id, category_id)
    link_article_category(conn, article_id, category_id)
    count = conn.execute("SELECT COUNT(*) FROM article_categories").fetchone()[0]
    assert count == 1


# (j) link_article_tag 멱등 — 동일 페어 두 번 호출 후 1행만 존재
def test_link_article_tag_idempotent(conn):
    feed_id = upsert_feed(conn, "Feed H", "https://h.example.com/rss")
    article_id = _insert_test_article(conn, feed_id, url_hash="hash_h", title_hash="th_h")
    tag_id = upsert_tag(conn, "python")
    link_article_tag(conn, article_id, tag_id)
    link_article_tag(conn, article_id, tag_id)
    count = conn.execute("SELECT COUNT(*) FROM article_tags").fetchone()[0]
    assert count == 1


# (k) insert_magazine 정상 + kind 제약
def test_insert_magazine_normal_and_kind_constraint(conn):
    mag_id = insert_magazine(conn, kind="daily", published_at="2026-05-05", file_path="/output/2026-05-05.md")
    assert isinstance(mag_id, int)
    count = conn.execute("SELECT COUNT(*) FROM magazines").fetchone()[0]
    assert count == 1
    with pytest.raises(sqlite3.IntegrityError):
        insert_magazine(conn, kind="invalid", published_at="2026-05-05", file_path="/output/bad.md")


# (l) link_magazine_article 멱등 — 동일 페어 두 번 호출 후 1행만 존재
def test_link_magazine_article_idempotent(conn):
    feed_id = upsert_feed(conn, "Feed I", "https://i.example.com/rss")
    article_id = _insert_test_article(conn, feed_id, url_hash="hash_i", title_hash="th_i")
    mag_id = insert_magazine(conn, kind="weekly", published_at="2026-05-05", file_path="/output/week.md")
    link_magazine_article(conn, mag_id, article_id)
    link_magazine_article(conn, mag_id, article_id)
    count = conn.execute("SELECT COUNT(*) FROM magazine_articles").fetchone()[0]
    assert count == 1


# (m) record_feed_success — 카운터를 0으로 리셋하고 last_success_at을 설정
def test_record_feed_success_resets_counter_and_sets_last_success_at(conn):
    feed_id = upsert_feed(conn, "Feed J", "https://j.example.com/rss")
    record_feed_failure(conn, feed_id)
    record_feed_failure(conn, feed_id)
    row = get_feed_by_url(conn, "https://j.example.com/rss")
    assert row["consecutive_failures"] == 2
    record_feed_success(conn, feed_id)
    row = get_feed_by_url(conn, "https://j.example.com/rss")
    assert row["consecutive_failures"] == 0
    assert row["last_success_at"] is not None
    assert isinstance(row["last_success_at"], str)


# (n) record_feed_failure — 카운터를 3회 누적
def test_record_feed_failure_increments_counter(conn):
    feed_id = upsert_feed(conn, "Feed K", "https://k.example.com/rss")
    record_feed_failure(conn, feed_id)
    record_feed_failure(conn, feed_id)
    record_feed_failure(conn, feed_id)
    row = get_feed_by_url(conn, "https://k.example.com/rss")
    assert row["consecutive_failures"] == 3


# (o) list_failing_feeds — threshold 이상 피드 필터링 및 정렬
def test_list_failing_feeds_filters_by_threshold(conn):
    feed_id1 = upsert_feed(conn, "Feed L", "https://l.example.com/rss")
    feed_id2 = upsert_feed(conn, "Feed M", "https://m.example.com/rss")
    feed_id3 = upsert_feed(conn, "Feed N", "https://n.example.com/rss")
    for _ in range(2):
        record_feed_failure(conn, feed_id1)
    for _ in range(5):
        record_feed_failure(conn, feed_id2)
    for _ in range(7):
        record_feed_failure(conn, feed_id3)
    results = list_failing_feeds(conn, threshold=5)
    assert len(results) == 2
    assert results[0]["consecutive_failures"] == 7


# (p) list_categories — 정규화된 이름 알파벳 정렬 반환
def test_list_categories_returns_normalized_names_sorted(conn):
    upsert_category(conn, "Zeta")
    upsert_category(conn, "alpha")
    names = [r["name"] for r in list_categories(conn)]
    assert names == ["alpha", "zeta"]


# (q) list_articles_by_ids — 해당 id 행만 반환, 빈 입력 시 []
def test_list_articles_by_ids_returns_only_matching(conn):
    feed_id = upsert_feed(conn, "Feed Q", "https://q.example.com/rss")
    id1 = _insert_test_article(conn, feed_id, url_hash="hq1", title_hash="tq1")
    _insert_test_article(conn, feed_id, url_hash="hq2", title_hash="tq2")
    id3 = _insert_test_article(conn, feed_id, url_hash="hq3", title_hash="tq3")
    rows = list_articles_by_ids(conn, [id1, id3])
    assert len(rows) == 2
    assert rows[0]["id"] == id1
    assert rows[1]["id"] == id3
    assert list_articles_by_ids(conn, []) == []


# (r) update_article_summary — 행 갱신, 존재하지 않는 id는 예외 없이 통과
def test_update_article_summary_updates_row(conn):
    feed_id = upsert_feed(conn, "Feed R", "https://r.example.com/rss")
    article_id = _insert_test_article(conn, feed_id, url_hash="hr1", title_hash="tr1")
    update_article_summary(conn, article_id=article_id, summary="새요약")
    row = get_article_by_url_hash(conn, "hr1")
    assert row["summary"] == "새요약"
    # 존재하지 않는 id — 예외 없이 통과
    update_article_summary(conn, article_id=99999, summary="없음")


# (s) list_categories_for_article — 연결된 카테고리만 name ASC 반환
def test_list_categories_for_article_returns_linked_only_sorted(conn):
    feed_id = upsert_feed(conn, "Feed S", "https://s.example.com/rss")
    article_id1 = _insert_test_article(conn, feed_id, url_hash="hs1", title_hash="ts1")
    article_id2 = _insert_test_article(conn, feed_id, url_hash="hs2", title_hash="ts2")
    article_id3 = _insert_test_article(conn, feed_id, url_hash="hs3", title_hash="ts3")

    cat1 = upsert_category(conn, "backend")
    cat2 = upsert_category(conn, "frontend")
    cat3 = upsert_category(conn, "ai")

    link_article_category(conn, article_id1, cat1)
    link_article_category(conn, article_id1, cat3)
    link_article_category(conn, article_id2, cat2)

    rows1 = list_categories_for_article(conn, article_id1)
    assert len(rows1) == 2
    assert [r["name"] for r in rows1] == ["ai", "backend"]

    rows2 = list_categories_for_article(conn, article_id2)
    assert len(rows2) == 1
    assert rows2[0]["name"] == "frontend"

    rows3 = list_categories_for_article(conn, article_id3)
    assert rows3 == []


# (t) list_tags_for_article — 연결된 태그만 name ASC 반환
def test_list_tags_for_article_returns_linked_only_sorted(conn):
    feed_id = upsert_feed(conn, "Feed T", "https://t.example.com/rss")
    article_id1 = _insert_test_article(conn, feed_id, url_hash="ht1", title_hash="tt1")
    article_id2 = _insert_test_article(conn, feed_id, url_hash="ht2", title_hash="tt2")
    article_id3 = _insert_test_article(conn, feed_id, url_hash="ht3", title_hash="tt3")

    tag1 = upsert_tag(conn, "python")
    tag2 = upsert_tag(conn, "rust")
    tag3 = upsert_tag(conn, "golang")

    link_article_tag(conn, article_id1, tag1)
    link_article_tag(conn, article_id1, tag3)
    link_article_tag(conn, article_id2, tag2)

    rows1 = list_tags_for_article(conn, article_id1)
    assert len(rows1) == 2
    assert [r["name"] for r in rows1] == ["golang", "python"]

    rows2 = list_tags_for_article(conn, article_id2)
    assert len(rows2) == 1
    assert rows2[0]["name"] == "rust"

    rows3 = list_tags_for_article(conn, article_id3)
    assert rows3 == []


# (u) list_tags — 모든 태그 name ASC 반환
def test_list_tags_returns_all_sorted_by_name(conn):
    upsert_tag(conn, "Beta")
    upsert_tag(conn, "alpha")
    upsert_tag(conn, "gamma")
    rows = list_tags(conn)
    assert len(rows) == 3
    assert [r["name"] for r in rows] == ["alpha", "beta", "gamma"]


# (v) list_articles_by_category — published_at DESC NULLS LAST, id DESC 정렬 + 미링크 카테고리 빈 리스트
def test_list_articles_by_category_orders_by_published_at_desc_nulls_last(conn):
    feed_id = upsert_feed(conn, "Feed V", "https://v.example.com/rss")
    cat_id = upsert_category(conn, "ai")
    cat_other_id = upsert_category(conn, "other")

    id1 = insert_article(
        conn, feed_id=feed_id, url="https://v.example.com/a1", url_hash="hv1",
        title="A1", title_hash="tv1", published_at="2026-05-01",
        content=None, summary=None,
    )
    id2 = insert_article(
        conn, feed_id=feed_id, url="https://v.example.com/a2", url_hash="hv2",
        title="A2", title_hash="tv2", published_at="2026-05-03",
        content=None, summary=None,
    )
    id3 = insert_article(
        conn, feed_id=feed_id, url="https://v.example.com/a3", url_hash="hv3",
        title="A3", title_hash="tv3", published_at=None,
        content=None, summary=None,
    )

    link_article_category(conn, id1, cat_id)
    link_article_category(conn, id2, cat_id)
    link_article_category(conn, id3, cat_id)

    rows = list_articles_by_category(conn, cat_id)
    assert len(rows) == 3
    assert [r["published_at"] for r in rows] == ["2026-05-03", "2026-05-01", None]

    assert list_articles_by_category(conn, cat_other_id) == []


# (w) list_articles_by_tag — published_at DESC NULLS LAST, id DESC 정렬 + 미링크 태그 빈 리스트
def test_list_articles_by_tag_orders_by_published_at_desc_nulls_last(conn):
    feed_id = upsert_feed(conn, "Feed W", "https://w.example.com/rss")
    tag_id = upsert_tag(conn, "ml")
    tag_other_id = upsert_tag(conn, "other")

    id1 = insert_article(
        conn, feed_id=feed_id, url="https://w.example.com/a1", url_hash="hw1",
        title="B1", title_hash="tw1", published_at="2026-05-01",
        content=None, summary=None,
    )
    id2 = insert_article(
        conn, feed_id=feed_id, url="https://w.example.com/a2", url_hash="hw2",
        title="B2", title_hash="tw2", published_at="2026-05-03",
        content=None, summary=None,
    )
    id3 = insert_article(
        conn, feed_id=feed_id, url="https://w.example.com/a3", url_hash="hw3",
        title="B3", title_hash="tw3", published_at=None,
        content=None, summary=None,
    )

    link_article_tag(conn, id1, tag_id)
    link_article_tag(conn, id2, tag_id)
    link_article_tag(conn, id3, tag_id)

    rows = list_articles_by_tag(conn, tag_id)
    assert len(rows) == 3
    assert [r["published_at"] for r in rows] == ["2026-05-03", "2026-05-01", None]

    assert list_articles_by_tag(conn, tag_other_id) == []


# (x) list_articles_published_between — 범위 내 글만 ASC 반환, NULL 제외
def test_list_articles_published_between_returns_only_in_range_and_sorted(conn):
    feed_id = upsert_feed(conn, "Feed X", "https://x.example.com/rss")

    # 글1: published_at=None
    insert_article(
        conn, feed_id=feed_id, url="https://x.example.com/a1", url_hash="hx1",
        title="글1", title_hash="tx1", published_at=None,
        content=None, summary=None,
    )
    # 글2: published_at="2026-04-25" (범위 미만)
    insert_article(
        conn, feed_id=feed_id, url="https://x.example.com/a2", url_hash="hx2",
        title="글2", title_hash="tx2", published_at="2026-04-25",
        content=None, summary=None,
    )
    # 글3: published_at="2026-04-29" (start_date == published_at, 포함)
    id3 = insert_article(
        conn, feed_id=feed_id, url="https://x.example.com/a3", url_hash="hx3",
        title="글3", title_hash="tx3", published_at="2026-04-29",
        content=None, summary=None,
    )
    # 글4: published_at="2026-05-01" (end_date == published_at, 포함)
    id4 = insert_article(
        conn, feed_id=feed_id, url="https://x.example.com/a4", url_hash="hx4",
        title="글4", title_hash="tx4", published_at="2026-05-01",
        content=None, summary=None,
    )
    # 글5: published_at="2026-05-02" (범위 초과)
    insert_article(
        conn, feed_id=feed_id, url="https://x.example.com/a5", url_hash="hx5",
        title="글5", title_hash="tx5", published_at="2026-05-02",
        content=None, summary=None,
    )

    rows = list_articles_published_between(conn, start_date="2026-04-29", end_date="2026-05-01")
    assert len(rows) == 2
    assert rows[0]["id"] == id3
    assert rows[1]["id"] == id4

    # 미래 범위 — 빈 리스트
    empty = list_articles_published_between(conn, start_date="2099-01-01", end_date="2099-12-31")
    assert empty == []


# (y) list_unanalyzed_article_ids — summary NULL 또는 빈 문자열인 글 id만 반환 (id ASC)
def test_list_unanalyzed_article_ids_returns_summary_null_and_empty(conn):
    feed_id = upsert_feed(conn, "Feed Y", "https://y.example.com/rss")

    id_a = insert_article(
        conn, feed_id=feed_id, url="https://y.example.com/a1", url_hash="hy1",
        title="글A", title_hash="ty1", published_at="2026-05-01",
        content="본문A", summary=None,
    )
    id_b = insert_article(
        conn, feed_id=feed_id, url="https://y.example.com/a2", url_hash="hy2",
        title="글B", title_hash="ty2", published_at="2026-05-02",
        content="본문B", summary="",
    )
    insert_article(
        conn, feed_id=feed_id, url="https://y.example.com/a3", url_hash="hy3",
        title="글C", title_hash="ty3", published_at="2026-05-03",
        content="본문C", summary="ok",
    )
    insert_article(
        conn, feed_id=feed_id, url="https://y.example.com/a4", url_hash="hy4",
        title="글D", title_hash="ty4", published_at="2026-05-04",
        content="본문D", summary="요약",
    )

    result = list_unanalyzed_article_ids(conn)
    assert result == [id_a, id_b]


# T-018A 테스트 케이스 7개

# (z1) init_db_idempotent_migration — 구 스키마 DB에 init_db 호출 후 신규 3 컬럼 존재
def test_init_db_idempotent_migration(tmp_path):
    db_path = tmp_path / "old.db"
    conn_old = sqlite3.connect(db_path)
    conn_old.execute("""
        CREATE TABLE feeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            consecutive_failures INTEGER NOT NULL DEFAULT 0,
            last_success_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn_old.commit()
    conn_old.close()

    init_db(db_path)

    conn_check = get_connection(db_path)
    try:
        cols = {row["name"] for row in conn_check.execute("PRAGMA table_info(feeds)").fetchall()}
    finally:
        conn_check.close()
    assert "enabled" in cols
    assert "last_fetched_at" in cols
    assert "updated_at" in cols


def test_init_db_feeds_migration_preserves_rows_and_defaults(tmp_path):
    db_path = tmp_path / "old_with_rows.db"
    conn_old = sqlite3.connect(db_path)
    conn_old.execute("""
        CREATE TABLE feeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            consecutive_failures INTEGER NOT NULL DEFAULT 0,
            last_success_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn_old.execute(
        "INSERT INTO feeds (name, url, consecutive_failures) VALUES (?, ?, ?)",
        ("Legacy Feed", "https://legacy.example.com/rss", 2),
    )
    conn_old.commit()
    conn_old.close()

    init_db(db_path)

    conn_check = get_connection(db_path)
    try:
        cols = {
            row["name"]: row
            for row in conn_check.execute("PRAGMA table_info(feeds)").fetchall()
        }
        row = conn_check.execute("SELECT * FROM feeds").fetchone()
        conn_check.execute(
            "INSERT INTO feeds (name, url) VALUES (?, ?)",
            ("New Feed", "https://new.example.com/rss"),
        )
        new_row = conn_check.execute(
            "SELECT * FROM feeds WHERE url = ?",
            ("https://new.example.com/rss",),
        ).fetchone()
    finally:
        conn_check.close()

    assert cols["updated_at"]["notnull"] == 1
    assert row["name"] == "Legacy Feed"
    assert row["consecutive_failures"] == 2
    assert row["enabled"] == 1
    assert row["updated_at"] is not None
    assert new_row["updated_at"] is not None


# (z2) init_db_double_call — 신 스키마에 init_db 두 번 호출해도 에러 없이 멱등
def test_init_db_double_call(tmp_path):
    db_path = tmp_path / "new.db"
    init_db(db_path)
    init_db(db_path)
    conn_check = get_connection(db_path)
    try:
        cols = {row["name"] for row in conn_check.execute("PRAGMA table_info(feeds)").fetchall()}
    finally:
        conn_check.close()
    assert "enabled" in cols
    assert "last_fetched_at" in cols
    assert "updated_at" in cols


# (z3) list_feeds_default — 전체 반환, id ASC 정렬
def test_list_feeds_default(conn):
    id1 = upsert_feed(conn, "Feed Alpha", "https://alpha.example.com/rss")
    id2 = upsert_feed(conn, "Feed Beta", "https://beta.example.com/rss")
    id3 = upsert_feed(conn, "Feed Gamma", "https://gamma.example.com/rss")
    set_feed_enabled(conn, id2, False)

    rows = list_feeds(conn)
    assert len(rows) == 3
    assert [r["id"] for r in rows] == [id1, id2, id3]


# (z4) list_feeds_enabled_only — enabled=1 피드만 반환
def test_list_feeds_enabled_only(conn):
    id1 = upsert_feed(conn, "Feed Alpha", "https://alpha.example.com/rss")
    id2 = upsert_feed(conn, "Feed Beta", "https://beta.example.com/rss")
    id3 = upsert_feed(conn, "Feed Gamma", "https://gamma.example.com/rss")
    set_feed_enabled(conn, id2, False)

    rows = list_feeds(conn, enabled_only=True)
    assert len(rows) == 2
    assert [r["id"] for r in rows] == [id1, id3]


# (z5) update_feed_changes_name_and_updated_at — name 변경, updated_at >= 이전 값
def test_update_feed_changes_name_and_updated_at(conn):
    feed_id = upsert_feed(conn, "OldName", "https://upd.example.com/rss")
    row_before = conn.execute("SELECT * FROM feeds WHERE id = ?", (feed_id,)).fetchone()
    updated_at_before = row_before["updated_at"]

    update_feed(conn, feed_id, name="NewName")

    row_after = conn.execute("SELECT * FROM feeds WHERE id = ?", (feed_id,)).fetchone()
    assert row_after["name"] == "NewName"
    assert row_after["updated_at"] >= updated_at_before


# (z6) set_feed_enabled_toggle — True→1, False→0, updated_at 갱신
def test_set_feed_enabled_toggle(conn):
    feed_id = upsert_feed(conn, "Toggle Feed", "https://toggle.example.com/rss")
    row = conn.execute("SELECT * FROM feeds WHERE id = ?", (feed_id,)).fetchone()
    assert row["enabled"] == 1

    set_feed_enabled(conn, feed_id, False)
    row = conn.execute("SELECT * FROM feeds WHERE id = ?", (feed_id,)).fetchone()
    assert row["enabled"] == 0
    assert row["updated_at"] is not None

    set_feed_enabled(conn, feed_id, True)
    row = conn.execute("SELECT * FROM feeds WHERE id = ?", (feed_id,)).fetchone()
    assert row["enabled"] == 1


# (z7) reset_feed_failures — consecutive_failures 5 → 0
def test_reset_feed_failures(conn):
    feed_id = upsert_feed(conn, "Failing Feed", "https://fail.example.com/rss")
    for _ in range(5):
        record_feed_failure(conn, feed_id)
    row = conn.execute("SELECT * FROM feeds WHERE id = ?", (feed_id,)).fetchone()
    assert row["consecutive_failures"] == 5

    reset_feed_failures(conn, feed_id)
    row = conn.execute("SELECT * FROM feeds WHERE id = ?", (feed_id,)).fetchone()
    assert row["consecutive_failures"] == 0


# T-018B2 테스트 케이스 6개

# T-018A가 이미 적용된 feeds DDL (enabled/last_fetched_at/updated_at 포함)
_FEEDS_MIGRATED_DDL = """
    CREATE TABLE feeds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE,
        consecutive_failures INTEGER NOT NULL DEFAULT 0,
        last_success_at TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        enabled INTEGER NOT NULL DEFAULT 1,
        last_fetched_at TEXT,
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
"""


# (z8) init_db_articles_feed_id_nullable_migration — 구 NOT NULL → init_db → nullable 확인
def test_init_db_articles_feed_id_nullable_migration(tmp_path):
    db_path = tmp_path / "old_articles.db"
    conn_old = sqlite3.connect(db_path)
    conn_old.executescript(
        _FEEDS_MIGRATED_DDL
        + """
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_id INTEGER NOT NULL REFERENCES feeds(id),
            url TEXT NOT NULL,
            url_hash TEXT NOT NULL UNIQUE,
            title TEXT,
            title_hash TEXT,
            published_at TEXT,
            content TEXT,
            summary TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_articles_url_hash ON articles(url_hash);
        CREATE INDEX IF NOT EXISTS idx_articles_title_hash ON articles(title_hash);
    """
    )
    conn_old.execute("INSERT INTO feeds (name, url) VALUES ('Feed A', 'https://a.example.com/rss')")
    feed_id = conn_old.execute("SELECT id FROM feeds WHERE url = 'https://a.example.com/rss'").fetchone()[0]
    conn_old.execute("INSERT INTO articles (feed_id, url, url_hash) VALUES (?, 'https://a.example.com/1', 'mg_hash1')", (feed_id,))
    conn_old.execute("INSERT INTO articles (feed_id, url, url_hash) VALUES (?, 'https://a.example.com/2', 'mg_hash2')", (feed_id,))
    conn_old.commit()
    original_count = conn_old.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    conn_old.close()

    init_db(db_path)

    conn_check = get_connection(db_path)
    try:
        cols = {row["name"]: row for row in conn_check.execute("PRAGMA table_info(articles)").fetchall()}
        assert cols["feed_id"]["notnull"] == 0
        indexes = {row["name"] for row in conn_check.execute("PRAGMA index_list(articles)").fetchall()}
        assert "idx_articles_url_hash" in indexes
        assert "idx_articles_title_hash" in indexes
        count = conn_check.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        assert count == original_count
    finally:
        conn_check.close()


# (z9) init_db_articles_snapshot_columns_migration — nullable + 스냅샷 컬럼 누락 → init_db → 두 컬럼 존재
def test_init_db_articles_snapshot_columns_migration(tmp_path):
    db_path = tmp_path / "nullable_no_snapshot.db"
    conn_old = sqlite3.connect(db_path)
    conn_old.executescript(
        _FEEDS_MIGRATED_DDL
        + """
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_id INTEGER REFERENCES feeds(id),
            url TEXT NOT NULL,
            url_hash TEXT NOT NULL UNIQUE,
            title TEXT,
            title_hash TEXT,
            published_at TEXT,
            content TEXT,
            summary TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """
    )
    conn_old.commit()
    conn_old.close()

    init_db(db_path)

    conn_check = get_connection(db_path)
    try:
        cols = {row["name"] for row in conn_check.execute("PRAGMA table_info(articles)").fetchall()}
        assert "feed_url_snapshot" in cols
        assert "feed_name_snapshot" in cols
    finally:
        conn_check.close()


# (z10) init_db_articles_migration_preserves_data — 구 스키마 + 데이터 → init_db → 원본 값 보존
def test_init_db_articles_migration_preserves_data(tmp_path):
    db_path = tmp_path / "preserve_data.db"
    conn_old = sqlite3.connect(db_path)
    conn_old.executescript(
        _FEEDS_MIGRATED_DDL
        + """
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_id INTEGER NOT NULL REFERENCES feeds(id),
            url TEXT NOT NULL,
            url_hash TEXT NOT NULL UNIQUE,
            title TEXT,
            title_hash TEXT,
            published_at TEXT,
            content TEXT,
            summary TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """
    )
    conn_old.execute("INSERT INTO feeds (name, url) VALUES ('Feed B', 'https://b.example.com/rss')")
    feed_id = conn_old.execute("SELECT id FROM feeds WHERE url = 'https://b.example.com/rss'").fetchone()[0]
    conn_old.execute(
        "INSERT INTO articles (feed_id, url, url_hash, title, title_hash, published_at, summary) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (feed_id, "https://b.example.com/1", "abc123", "원본 제목", "titlehash1", "2026-05-01", "원본 요약"),
    )
    conn_old.commit()
    conn_old.close()

    init_db(db_path)

    conn_check = get_connection(db_path)
    try:
        row = conn_check.execute("SELECT * FROM articles WHERE url_hash = 'abc123'").fetchone()
        assert row is not None
        assert row["title"] == "원본 제목"
        assert row["title_hash"] == "titlehash1"
        assert row["published_at"] == "2026-05-01"
        assert row["summary"] == "원본 요약"
        assert row["url"] == "https://b.example.com/1"
    finally:
        conn_check.close()


# (z11) init_db_articles_double_call — 신 스키마 DB에 init_db 두 번 → 멱등, 데이터 보존
def test_init_db_articles_double_call(tmp_path):
    db_path = tmp_path / "double.db"
    init_db(db_path)

    c = get_connection(db_path)
    try:
        c.execute("INSERT INTO feeds (name, url) VALUES ('Feed C', 'https://c.example.com/rss')")
        feed_id = c.execute("SELECT id FROM feeds WHERE url = 'https://c.example.com/rss'").fetchone()["id"]
        c.execute(
            "INSERT INTO articles (feed_id, url, url_hash) VALUES (?, 'https://c.example.com/1', 'hash_dc1')",
            (feed_id,),
        )
        c.commit()
    finally:
        c.close()

    init_db(db_path)

    conn_check = get_connection(db_path)
    try:
        count = conn_check.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        assert count == 1
        col_names = [row["name"] for row in conn_check.execute("PRAGMA table_info(articles)").fetchall()]
        assert col_names.count("feed_url_snapshot") == 1
        assert col_names.count("feed_name_snapshot") == 1
    finally:
        conn_check.close()


# (z12) delete_feed_fills_snapshot_and_nulls_feed_id — 스냅샷 채움, feed_id NULL, feeds 행 삭제
def test_delete_feed_fills_snapshot_and_nulls_feed_id(conn):
    feed_id = upsert_feed(conn, "X", "https://x.example.com/rss")
    art_id1 = insert_article(
        conn,
        feed_id=feed_id,
        url="https://x.example.com/a1",
        url_hash="hx_del1",
        title="Article 1",
        title_hash="tx_del1",
        published_at="2026-05-01",
        content=None,
        summary=None,
    )
    art_id2 = insert_article(
        conn,
        feed_id=feed_id,
        url="https://x.example.com/a2",
        url_hash="hx_del2",
        title="Article 2",
        title_hash="tx_del2",
        published_at="2026-05-02",
        content=None,
        summary=None,
    )

    delete_feed(conn, feed_id)

    rows = conn.execute(
        "SELECT feed_id, feed_url_snapshot, feed_name_snapshot FROM articles WHERE id IN (?, ?)",
        (art_id1, art_id2),
    ).fetchall()
    assert len(rows) == 2
    for row in rows:
        assert row["feed_id"] is None
        assert row["feed_url_snapshot"] == "https://x.example.com/rss"
        assert row["feed_name_snapshot"] == "X"

    count = conn.execute("SELECT COUNT(*) FROM feeds WHERE id = ?", (feed_id,)).fetchone()[0]
    assert count == 0


# (z13) delete_feed_no_articles — articles 0건일 때 feeds 행만 삭제, 예외 없음
def test_delete_feed_no_articles(conn):
    feed_id = upsert_feed(conn, "Y", "https://y.example.com/rss")

    delete_feed(conn, feed_id)

    count = conn.execute("SELECT COUNT(*) FROM feeds WHERE id = ?", (feed_id,)).fetchone()[0]
    assert count == 0
    art_count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    assert art_count == 0


# (z14) update_feed_url — url 인자 전달 시 feeds.url 변경
def test_update_feed_url_changes_url(conn):
    feed_id = upsert_feed(conn, "Old", "https://a.example.com/rss")
    conn.commit()

    update_feed(conn, feed_id, name="Old", url="https://b.example.com/rss")
    conn.commit()

    from rss_wiki.storage.repo import get_feed_by_id
    row = get_feed_by_id(conn, feed_id)
    assert row["url"] == "https://b.example.com/rss"


# (z15) update_feed_url_duplicate_raises — 다른 피드와 동일 url로 변경 시 IntegrityError
def test_update_feed_url_duplicate_raises(conn):
    feed_a_id = upsert_feed(conn, "A", "https://a.example.com/rss")
    feed_b_id = upsert_feed(conn, "B", "https://b.example.com/rss")
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        update_feed(conn, feed_b_id, name="B", url="https://a.example.com/rss")
