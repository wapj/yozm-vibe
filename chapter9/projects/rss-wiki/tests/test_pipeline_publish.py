from __future__ import annotations

import logging
import pytest

from rss_wiki.storage.db import get_connection, init_db
from rss_wiki.storage.repo import (
    insert_article,
    link_article_category,
    link_article_tag,
    record_feed_failure,
    upsert_category,
    upsert_feed,
    upsert_tag,
)
from rss_wiki.pipeline.llm import AnalyzeResult, AnalyzeStats
from rss_wiki.pipeline.publish import publish_daily, publish_indexes, publish_monthly, publish_weekly


@pytest.fixture
def conn(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    c = get_connection(db_path)
    yield c
    c.close()


def _make_feed(conn):
    return upsert_feed(conn, "TestFeed", "https://example.com/rss")


def _make_article(conn, feed_id, *, url_suffix="1", title="글제목", summary="요약"):
    return insert_article(
        conn,
        feed_id=feed_id,
        url=f"https://example.com/article/{url_suffix}",
        url_hash=f"hash_{url_suffix}",
        title=title,
        title_hash=f"th_{url_suffix}",
        published_at="2026-05-05T00:00:00",
        content="본문",
        summary=summary,
    )


def _make_result(analyzed_ids, trends=None):
    return AnalyzeResult(
        stats=AnalyzeStats(len(analyzed_ids), len(analyzed_ids), 0, 0, 0),
        trends=trends or {},
        analyzed_article_ids=tuple(analyzed_ids),
    )


def test_publish_daily_raises_on_empty_analyzed_ids(conn, tmp_path):
    result = AnalyzeResult(
        stats=AnalyzeStats(0, 0, 0, 0, 0),
        trends={},
        analyzed_article_ids=(),
    )
    output_dir = tmp_path / "output"
    with pytest.raises(ValueError):
        publish_daily(conn=conn, result=result, output_dir=output_dir, date="2026-05-05")
    assert not output_dir.exists() or not (output_dir / "daily-2026-05-05.md").exists()
    count = conn.execute("SELECT COUNT(*) FROM magazines").fetchone()[0]
    assert count == 0


def test_publish_daily_writes_file_and_inserts_magazine(conn, tmp_path):
    feed_id = _make_feed(conn)
    article_id = _make_article(conn, feed_id, url_suffix="w1", title="AI글제목", summary="요약")
    cat_id = upsert_category(conn, "AI")
    link_article_category(conn, article_id, cat_id)

    result = _make_result([article_id], trends={"ai": "트렌드 단락"})
    output_dir = tmp_path / "output"

    path = publish_daily(conn=conn, result=result, output_dir=output_dir, date="2026-05-05")

    assert path == output_dir / "daily-2026-05-05.md"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "# 일간 매거진" in content
    assert "## ai" in content
    assert "> 트렌드 단락" in content
    assert "### AI글제목" in content
    assert "요약" in content

    mag_row = conn.execute("SELECT * FROM magazines").fetchone()
    assert mag_row is not None
    assert mag_row["kind"] == "daily"
    assert mag_row["file_path"] == str(path)

    link_count = conn.execute("SELECT COUNT(*) FROM magazine_articles").fetchone()[0]
    assert link_count == 1


def test_publish_daily_groups_by_first_category(conn, tmp_path):
    feed_id = _make_feed(conn)
    article_id = _make_article(conn, feed_id, url_suffix="gc1", title="글", summary="요약")
    # backend, ai — name ASC 정렬상 "ai"가 먼저
    cat_ai = upsert_category(conn, "ai")
    cat_backend = upsert_category(conn, "backend")
    link_article_category(conn, article_id, cat_ai)
    link_article_category(conn, article_id, cat_backend)

    result = _make_result([article_id], trends={"ai": "AI트렌드"})
    output_dir = tmp_path / "output"

    path = publish_daily(conn=conn, result=result, output_dir=output_dir, date="2026-05-05")
    content = path.read_text(encoding="utf-8")

    assert content.count("## ai") == 1
    assert "## backend" not in content


def test_publish_daily_skips_articles_without_category(conn, tmp_path, caplog):
    feed_id = _make_feed(conn)
    id1 = _make_article(conn, feed_id, url_suffix="sk1", title="글1", summary="요약1")
    id2 = _make_article(conn, feed_id, url_suffix="sk2", title="글2", summary="요약2")
    cat_id = upsert_category(conn, "ai")
    link_article_category(conn, id1, cat_id)
    # id2는 카테고리 미링크

    result = _make_result([id1, id2], trends={"ai": "트렌드"})
    output_dir = tmp_path / "output"

    with caplog.at_level(logging.WARNING):
        path = publish_daily(conn=conn, result=result, output_dir=output_dir, date="2026-05-05")

    content = path.read_text(encoding="utf-8")
    assert "글1" in content
    assert "글2" not in content

    link_count = conn.execute("SELECT COUNT(*) FROM magazine_articles").fetchone()[0]
    assert link_count == 1
    aid_row = conn.execute("SELECT article_id FROM magazine_articles").fetchone()
    assert aid_row["article_id"] == id1

    assert str(id2) in caplog.text


def test_publish_daily_raises_when_no_article_has_category(conn, tmp_path):
    feed_id = _make_feed(conn)
    article_id = _make_article(conn, feed_id, url_suffix="nc1", title="글", summary="요약")
    # 카테고리 미링크

    result = _make_result([article_id])
    output_dir = tmp_path / "output"

    with pytest.raises(ValueError):
        publish_daily(conn=conn, result=result, output_dir=output_dir, date="2026-05-05")

    assert not (output_dir / "daily-2026-05-05.md").exists() if output_dir.exists() else True
    count = conn.execute("SELECT COUNT(*) FROM magazines").fetchone()[0]
    assert count == 0


def test_publish_daily_includes_failing_feeds_section(conn, tmp_path):
    feed_id = _make_feed(conn)
    for _ in range(5):
        record_feed_failure(conn, feed_id)
    article_id = _make_article(conn, feed_id, url_suffix="ff1", title="글", summary="요약")
    cat_id = upsert_category(conn, "ai")
    link_article_category(conn, article_id, cat_id)

    result = _make_result([article_id], trends={"ai": "트렌드"})
    output_dir = tmp_path / "output"

    path = publish_daily(conn=conn, result=result, output_dir=output_dir, date="2026-05-05")
    content = path.read_text(encoding="utf-8")

    assert "## 장애 피드" in content
    assert "TestFeed" in content


def test_publish_daily_uses_empty_trend_when_missing(conn, tmp_path):
    feed_id = _make_feed(conn)
    article_id = _make_article(conn, feed_id, url_suffix="et1", title="글", summary="요약")
    cat_id = upsert_category(conn, "ai")
    link_article_category(conn, article_id, cat_id)

    result = _make_result([article_id], trends={})
    output_dir = tmp_path / "output"

    path = publish_daily(conn=conn, result=result, output_dir=output_dir, date="2026-05-05")
    content = path.read_text(encoding="utf-8")

    assert "## ai" in content
    # 빈 트렌드 — ">" 블록인용 없음 (빈 문자열은 splitlines()가 빈 리스트 반환)
    lines = content.splitlines()
    blockquote_lines = [l for l in lines if l.startswith("> ")]
    assert len(blockquote_lines) == 0


# --- publish_indexes 테스트 ---

def _make_article_with_date(conn, feed_id, *, url_suffix, title="글제목", summary="요약", published_at="2026-05-05"):
    return insert_article(
        conn,
        feed_id=feed_id,
        url=f"https://example.com/idx/{url_suffix}",
        url_hash=f"idx_hash_{url_suffix}",
        title=title,
        title_hash=f"idx_th_{url_suffix}",
        published_at=published_at,
        content="본문",
        summary=summary,
    )


def test_publish_indexes_returns_empty_for_empty_db(conn, tmp_path):
    output_dir = tmp_path / "output"
    result = publish_indexes(conn=conn, output_dir=output_dir)
    assert result == []
    if output_dir.exists():
        assert list(output_dir.iterdir()) == []


def test_publish_indexes_writes_category_and_tag_files(conn, tmp_path):
    feed_id = _make_feed(conn)
    article_id = _make_article_with_date(conn, feed_id, url_suffix="wc1", title="제목", summary="요약", published_at="2026-05-05")
    cat_id = upsert_category(conn, "AI")
    link_article_category(conn, article_id, cat_id)
    tag_id = upsert_tag(conn, "tag1")
    link_article_tag(conn, article_id, tag_id)

    output_dir = tmp_path / "output"
    written = publish_indexes(conn=conn, output_dir=output_dir)

    assert len(written) == 2

    cat_file = output_dir / "index-category-ai.md"
    assert cat_file.exists()
    cat_content = cat_file.read_text(encoding="utf-8")
    assert "# 카테고리 — ai" in cat_content
    assert "## 2026-05-05" in cat_content
    assert "[제목](" in cat_content
    assert "요약" in cat_content

    tag_file = output_dir / "index-tag-tag1.md"
    assert tag_file.exists()
    tag_content = tag_file.read_text(encoding="utf-8")
    assert "# 태그 — tag1" in tag_content
    assert "## 2026-05-05" in tag_content
    assert "[제목](" in tag_content
    assert "요약" in tag_content


def test_publish_indexes_orders_by_published_at_desc(conn, tmp_path):
    feed_id = _make_feed(conn)
    cat_id = upsert_category(conn, "ai")

    for i, date in enumerate(["2026-05-01", "2026-05-03", "2026-05-05"]):
        aid = _make_article_with_date(conn, feed_id, url_suffix=f"ord{i}", title=f"글{i}", summary="요약", published_at=date)
        link_article_category(conn, aid, cat_id)

    output_dir = tmp_path / "output"
    publish_indexes(conn=conn, output_dir=output_dir)

    cat_file = output_dir / "index-category-ai.md"
    content = cat_file.read_text(encoding="utf-8")
    headers = [line for line in content.splitlines() if line.startswith("## ")]
    assert headers == ["## 2026-05-05", "## 2026-05-03", "## 2026-05-01"]


def test_publish_indexes_skips_empty_categories_and_tags(conn, tmp_path, caplog):
    feed_id = _make_feed(conn)
    upsert_category(conn, "empty")
    upsert_tag(conn, "tag-empty")

    cat_id = upsert_category(conn, "ai")
    aid = _make_article_with_date(conn, feed_id, url_suffix="skip1", title="글", summary="요약")
    link_article_category(conn, aid, cat_id)

    output_dir = tmp_path / "output"

    with caplog.at_level(logging.WARNING):
        written = publish_indexes(conn=conn, output_dir=output_dir)

    assert len(written) == 1
    assert not (output_dir / "index-category-empty.md").exists()
    assert not (output_dir / "index-tag-tag-empty.md").exists()
    assert "name=empty" in caplog.text
    assert "name=tag-empty" in caplog.text


def test_publish_indexes_overwrites_existing_files(conn, tmp_path):
    feed_id = _make_feed(conn)
    cat_id = upsert_category(conn, "ai")
    aid = _make_article_with_date(conn, feed_id, url_suffix="ow1", title="글", summary="요약")
    link_article_category(conn, aid, cat_id)

    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = output_dir / "index-category-ai.md"
    existing.write_text("OLD", encoding="utf-8")

    publish_indexes(conn=conn, output_dir=output_dir)

    content = existing.read_text(encoding="utf-8")
    assert "OLD" not in content
    assert "# 카테고리 — ai" in content


def test_publish_indexes_includes_article_in_multiple_category_indexes(conn, tmp_path):
    feed_id = _make_feed(conn)
    cat_ai = upsert_category(conn, "ai")
    cat_backend = upsert_category(conn, "backend")
    aid = _make_article_with_date(conn, feed_id, url_suffix="multi1", title="공통글", summary="공통요약")
    link_article_category(conn, aid, cat_ai)
    link_article_category(conn, aid, cat_backend)

    output_dir = tmp_path / "output"
    written = publish_indexes(conn=conn, output_dir=output_dir)

    assert len(written) == 2

    ai_content = (output_dir / "index-category-ai.md").read_text(encoding="utf-8")
    backend_content = (output_dir / "index-category-backend.md").read_text(encoding="utf-8")

    assert "[공통글](" in ai_content
    assert "[공통글](" in backend_content


# --- publish_weekly 테스트 ---

def _make_weekly_article(conn, feed_id, *, url_suffix, title, summary, published_at):
    from rss_wiki.storage.repo import insert_article as _insert
    return _insert(
        conn,
        feed_id=feed_id,
        url=f"https://example.com/weekly/{url_suffix}",
        url_hash=f"wh_{url_suffix}",
        title=title,
        title_hash=f"wth_{url_suffix}",
        published_at=published_at,
        content="본문",
        summary=summary,
    )


def test_publish_weekly_returns_none_for_empty_period(conn, tmp_path, caplog):
    calls = []
    fake_runner = lambda p: (calls.append(p), "x")[1]

    output_dir = tmp_path / "output"
    with caplog.at_level(logging.WARNING):
        result = publish_weekly(conn=conn, end_date="2026-05-01", output_dir=output_dir, runner=fake_runner)

    assert result is None
    assert not (output_dir / "weekly-2026-W18.md").exists() if not output_dir.exists() else not (output_dir / "weekly-2026-W18.md").exists()
    count = conn.execute("SELECT COUNT(*) FROM magazines").fetchone()[0]
    assert count == 0
    assert "start=2026-04-25" in caplog.text
    assert "end=2026-05-01" in caplog.text
    assert len(calls) == 0


def test_publish_weekly_writes_markdown_and_inserts_magazine(conn, tmp_path):
    feed_id = _make_feed(conn)
    calls = []

    id1 = _make_weekly_article(conn, feed_id, url_suffix="w1", title="AI 소식", summary="AI 요약", published_at="2026-04-29")
    id2 = _make_weekly_article(conn, feed_id, url_suffix="w2", title="백엔드 소식", summary="백엔드 요약", published_at="2026-04-30")
    id3 = _make_weekly_article(conn, feed_id, url_suffix="w3", title="클라우드 소식", summary="클라우드 요약", published_at="2026-05-01")

    fake_runner = lambda p: (calls.append(p), "이번 주는 AI 발전이 두드러졌습니다.")[1]
    output_dir = tmp_path / "output"

    path = publish_weekly(conn=conn, end_date="2026-05-01", output_dir=output_dir, runner=fake_runner)

    assert path == output_dir / "weekly-2026-W18.md"
    assert path.exists()

    content = path.read_text(encoding="utf-8")
    assert "# 주간 매거진 — 2026-W18" in content
    assert "## 통합 요약" in content
    assert "이번 주는 AI 발전이 두드러졌습니다." in content
    assert "## 출처" in content
    assert "[AI 소식](https://example.com/weekly/w1)" in content
    assert "[백엔드 소식](https://example.com/weekly/w2)" in content
    assert "[클라우드 소식](https://example.com/weekly/w3)" in content

    mag_row = conn.execute("SELECT * FROM magazines").fetchone()
    assert mag_row is not None
    assert mag_row["kind"] == "weekly"
    assert mag_row["published_at"] == "2026-05-01"

    link_count = conn.execute("SELECT COUNT(*) FROM magazine_articles").fetchone()[0]
    assert link_count == 3

    linked_ids = {r[0] for r in conn.execute("SELECT article_id FROM magazine_articles").fetchall()}
    assert linked_ids == {id1, id2, id3}

    assert len(calls) == 1


def test_publish_weekly_uses_period_label_from_end_date(conn, tmp_path):
    feed_id = _make_feed(conn)
    fake_runner = lambda p: "주간 통합 요약입니다."

    # 2026-05-08 은 ISO 주차 W19
    _make_weekly_article(conn, feed_id, url_suffix="pl1", title="글W19", summary="요약", published_at="2026-05-08")
    output_dir = tmp_path / "output"

    path = publish_weekly(conn=conn, end_date="2026-05-08", output_dir=output_dir, runner=fake_runner)
    assert path is not None
    assert path.name == "weekly-2026-W19.md"
    content = path.read_text(encoding="utf-8")
    assert content.splitlines()[0] == "# 주간 매거진 — 2026-W19"

    # 2026-01-02 은 ISO 주차 W01 (zero-pad 검증)
    _make_weekly_article(conn, feed_id, url_suffix="pl2", title="글W01", summary="요약", published_at="2026-01-02")
    path2 = publish_weekly(conn=conn, end_date="2026-01-02", output_dir=output_dir, runner=fake_runner)
    assert path2 is not None
    assert path2.name == "weekly-2026-W01.md"


def test_publish_weekly_excludes_articles_outside_period(conn, tmp_path):
    feed_id = _make_feed(conn)
    fake_runner = lambda p: "주간 통합 요약입니다."
    output_dir = tmp_path / "output"

    # 기간 내 (end_date="2026-05-01" → start_date="2026-04-25")
    id_in1 = _make_weekly_article(conn, feed_id, url_suffix="in1", title="기간내1", summary="요약", published_at="2026-04-26")
    id_in2 = _make_weekly_article(conn, feed_id, url_suffix="in2", title="기간내2", summary="요약", published_at="2026-04-29")
    id_in3 = _make_weekly_article(conn, feed_id, url_suffix="in3", title="기간내3", summary="요약", published_at="2026-05-01")

    # 기간 외
    _make_weekly_article(conn, feed_id, url_suffix="out1", title="기간외조기", summary="요약", published_at="2026-04-20")
    _make_weekly_article(conn, feed_id, url_suffix="out2", title="기간외초과", summary="요약", published_at="2026-05-02")
    # NULL published_at
    from rss_wiki.storage.repo import insert_article as _insert
    _insert(
        conn, feed_id=feed_id, url="https://example.com/weekly/null1",
        url_hash="wh_null1", title="기간외NULL", title_hash="wth_null1",
        published_at=None, content=None, summary="요약",
    )

    path = publish_weekly(conn=conn, end_date="2026-05-01", output_dir=output_dir, runner=fake_runner)

    assert path is not None
    assert path.exists()

    content = path.read_text(encoding="utf-8")
    assert "기간내1" in content
    assert "기간내2" in content
    assert "기간내3" in content
    assert "기간외조기" not in content
    assert "기간외초과" not in content
    assert "기간외NULL" not in content

    link_count = conn.execute("SELECT COUNT(*) FROM magazine_articles").fetchone()[0]
    assert link_count == 3

    linked_ids = {r[0] for r in conn.execute("SELECT article_id FROM magazine_articles").fetchall()}
    assert linked_ids == {id_in1, id_in2, id_in3}


# --- publish_monthly 테스트 ---

def _make_monthly_article(conn, feed_id, *, url_suffix, title, summary, published_at):
    from rss_wiki.storage.repo import insert_article as _insert
    return _insert(
        conn,
        feed_id=feed_id,
        url=f"https://example.com/monthly/{url_suffix}",
        url_hash=f"mh_{url_suffix}",
        title=title,
        title_hash=f"mth_{url_suffix}",
        published_at=published_at,
        content="본문",
        summary=summary,
    )


def test_publish_monthly_returns_none_for_empty_period(conn, tmp_path, caplog):
    calls = []
    fake_runner = lambda p: (calls.append(p), "x")[1]

    output_dir = tmp_path / "output"
    with caplog.at_level(logging.WARNING):
        result = publish_monthly(conn=conn, end_date="2026-05-29", output_dir=output_dir, runner=fake_runner)

    assert result is None
    assert not output_dir.exists() or not (output_dir / "monthly-2026-05.md").exists()
    count = conn.execute("SELECT COUNT(*) FROM magazines").fetchone()[0]
    assert count == 0
    assert "start=2026-05-01" in caplog.text
    assert "end=2026-05-29" in caplog.text
    assert len(calls) == 0


def test_publish_monthly_writes_markdown_and_inserts_magazine(conn, tmp_path):
    feed_id = _make_feed(conn)
    calls = []

    id1 = _make_monthly_article(conn, feed_id, url_suffix="m1", title="AI 소식", summary="AI 요약", published_at="2026-05-03")
    id2 = _make_monthly_article(conn, feed_id, url_suffix="m2", title="인프라 소식", summary="인프라 요약", published_at="2026-05-15")
    id3 = _make_monthly_article(conn, feed_id, url_suffix="m3", title="클라우드 소식", summary="클라우드 요약", published_at="2026-05-29")

    fake_runner = lambda p: (calls.append(p), "이번 달은 AI 발전과 인프라 안정화가 주요 주제였습니다.")[1]
    output_dir = tmp_path / "output"

    path = publish_monthly(conn=conn, end_date="2026-05-29", output_dir=output_dir, runner=fake_runner)

    assert path == output_dir / "monthly-2026-05.md"
    assert path.exists()

    content = path.read_text(encoding="utf-8")
    assert "# 월간 매거진 — 2026-05" in content
    assert "## 통합 요약" in content
    assert "이번 달은 AI 발전과 인프라 안정화가 주요 주제였습니다." in content
    assert "## 출처" in content
    assert "[AI 소식](https://example.com/monthly/m1)" in content
    assert "[인프라 소식](https://example.com/monthly/m2)" in content
    assert "[클라우드 소식](https://example.com/monthly/m3)" in content

    mag_row = conn.execute("SELECT * FROM magazines").fetchone()
    assert mag_row is not None
    assert mag_row["kind"] == "monthly"
    assert mag_row["published_at"] == "2026-05-29"

    link_count = conn.execute("SELECT COUNT(*) FROM magazine_articles").fetchone()[0]
    assert link_count == 3

    linked_ids = {r[0] for r in conn.execute("SELECT article_id FROM magazine_articles").fetchall()}
    assert linked_ids == {id1, id2, id3}

    assert len(calls) == 1


def test_publish_monthly_uses_period_label_from_end_date(conn, tmp_path):
    feed_id = _make_feed(conn)
    fake_runner = lambda p: "월간 통합 요약입니다."

    _make_monthly_article(conn, feed_id, url_suffix="pl1", title="1월글", summary="요약", published_at="2026-01-30")
    output_dir = tmp_path / "output"

    path = publish_monthly(conn=conn, end_date="2026-01-30", output_dir=output_dir, runner=fake_runner)
    assert path is not None
    assert path.name == "monthly-2026-01.md"
    content = path.read_text(encoding="utf-8")
    assert content.splitlines()[0] == "# 월간 매거진 — 2026-01"

    # 12월 zero-pad 검증
    _make_monthly_article(conn, feed_id, url_suffix="pl2", title="12월글", summary="요약", published_at="2026-12-25")
    path2 = publish_monthly(conn=conn, end_date="2026-12-25", output_dir=output_dir, runner=fake_runner)
    assert path2 is not None
    assert path2.name == "monthly-2026-12.md"


def test_publish_monthly_excludes_articles_outside_period(conn, tmp_path):
    feed_id = _make_feed(conn)
    fake_runner = lambda p: "월간 통합 요약입니다."
    output_dir = tmp_path / "output"

    # 기간 내 (end_date="2026-05-29" → start_date="2026-05-01", 양 끝 포함)
    id_in1 = _make_monthly_article(conn, feed_id, url_suffix="in1", title="기간내1", summary="요약", published_at="2026-05-01")
    id_in2 = _make_monthly_article(conn, feed_id, url_suffix="in2", title="기간내2", summary="요약", published_at="2026-05-15")
    id_in3 = _make_monthly_article(conn, feed_id, url_suffix="in3", title="기간내3", summary="요약", published_at="2026-05-29")

    # 기간 외
    _make_monthly_article(conn, feed_id, url_suffix="out1", title="기간외전월", summary="요약", published_at="2026-04-30")
    _make_monthly_article(conn, feed_id, url_suffix="out2", title="기간외초과", summary="요약", published_at="2026-05-30")
    from rss_wiki.storage.repo import insert_article as _insert
    _insert(
        conn, feed_id=feed_id, url="https://example.com/monthly/null1",
        url_hash="mh_null1", title="기간외NULL", title_hash="mth_null1",
        published_at=None, content=None, summary="요약",
    )

    path = publish_monthly(conn=conn, end_date="2026-05-29", output_dir=output_dir, runner=fake_runner)

    assert path is not None
    assert path.exists()

    content = path.read_text(encoding="utf-8")
    assert "기간내1" in content
    assert "기간내2" in content
    assert "기간내3" in content
    assert "기간외전월" not in content
    assert "기간외초과" not in content
    assert "기간외NULL" not in content

    link_count = conn.execute("SELECT COUNT(*) FROM magazine_articles").fetchone()[0]
    assert link_count == 3

    linked_ids = {r[0] for r in conn.execute("SELECT article_id FROM magazine_articles").fetchall()}
    assert linked_ids == {id_in1, id_in2, id_in3}
