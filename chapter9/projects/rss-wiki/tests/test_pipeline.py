import asyncio

from rss_wiki import extract as extract_module
from rss_wiki import ingest
from rss_wiki import pipeline
from rss_wiki import summarize as summarize_module


def _article(article_id, *, title, published="2026-07-07T00:00:00Z"):
    return {
        "id": article_id,
        "title": title,
        "link": f"https://example.com/{article_id}",
        "published": published,
        "description": f"{article_id} description",
        "content": None,
    }


def _fake_extract(article):
    return {"body": f"{article['id']} body", "source": "original"}


def _fake_summarize(article, body, *, feed_name):
    return {
        "summary": f"{body} 요약",
        "title": article["title"],
        "link": article["link"],
        "published": article["published"],
        "feed_name": feed_name,
    }


async def _fake_summarize_async(article, body, *, feed_name):
    return _fake_summarize(article, body, feed_name=feed_name)


def test_run_fetch_records_success_batch_and_state_meta():
    feeds = [{"name": "피드A", "url": "http://a"}]
    articles = [_article("a1", title="첫 글"), _article("a2", title="둘째 글")]

    def select(feed, state, *, limit):
        return articles

    result = pipeline.run_fetch(
        feeds,
        {"processed": {}},
        limit=10,
        now="2026-07-07T12:00:00",
        collected_date="2026-07-07",
        select=select,
        extract=_fake_extract,
        summarize=_fake_summarize,
    )

    assert [b["summary_result"]["title"] for b in result["batch"]] == ["첫 글", "둘째 글"]
    for article_id in ("a1", "a2"):
        record = result["state"]["processed"][article_id]
        assert record["status"] == "ok"
        assert record["processed_at"] == "2026-07-07T12:00:00"
        assert record["meta"]["published"] == "2026-07-07"
        assert record["meta"]["collected_date"] == "2026-07-07"
        assert record["meta"]["feed_name"] == "피드A"
        assert record["meta"]["filename"]
    assert result["report"]["feeds"] == {"succeeded": 1, "failed": 0, "failures": []}
    assert result["report"]["articles"]["succeeded"] == 2
    assert result["report"]["articles"]["failed"] == 0


def test_run_fetch_skips_feed_on_parse_error_and_continues_other_feeds():
    feeds = [{"name": "깨진피드", "url": "http://broken"}, {"name": "정상피드", "url": "http://ok"}]
    ok_articles = [_article("ok1", title="정상 글")]

    def select(feed, state, *, limit):
        if feed["name"] == "깨진피드":
            raise ingest.FeedParseError("파싱 실패")
        return ok_articles

    result = pipeline.run_fetch(
        feeds,
        {"processed": {}},
        limit=10,
        now="2026-07-07T12:00:00",
        collected_date="2026-07-07",
        select=select,
        extract=_fake_extract,
        summarize=_fake_summarize,
    )

    assert [b["summary_result"]["title"] for b in result["batch"]] == ["정상 글"]
    assert "ok1" in result["state"]["processed"]
    assert result["report"]["feeds"] == {
        "succeeded": 1,
        "failed": 1,
        "failures": [{"feed": "깨진피드", "reason": "파싱 실패"}],
    }


def test_run_fetch_skips_article_on_extraction_error_without_recording_state():
    feeds = [{"name": "피드A", "url": "http://a"}]
    articles = [_article("bad1", title="본문 실패 글"), _article("good1", title="정상 글")]

    def extract(article):
        if article["id"] == "bad1":
            raise extract_module.ArticleExtractionError("본문 확보 실패")
        return _fake_extract(article)

    result = pipeline.run_fetch(
        feeds,
        {"processed": {}},
        limit=10,
        now="2026-07-07T12:00:00",
        collected_date="2026-07-07",
        select=lambda feed, state, *, limit: articles,
        extract=extract,
        summarize=_fake_summarize,
    )

    assert [b["summary_result"]["title"] for b in result["batch"]] == ["정상 글"]
    assert "bad1" not in result["state"]["processed"]
    assert "good1" in result["state"]["processed"]
    assert result["report"]["articles"]["failed"] == 1
    assert result["report"]["articles"]["failures"] == [
        {"feed": "피드A", "article_id": "bad1", "reason": "본문 확보 실패"}
    ]
    assert result["report"]["articles"]["succeeded"] == 1


def test_run_fetch_skips_article_on_summarize_error_without_recording_state():
    feeds = [{"name": "피드A", "url": "http://a"}]
    articles = [_article("bad1", title="요약 실패 글"), _article("good1", title="정상 글")]

    def summarize(article, body, *, feed_name):
        if article["id"] == "bad1":
            raise summarize_module.SummarizeError("요약 실패")
        return _fake_summarize(article, body, feed_name=feed_name)

    result = pipeline.run_fetch(
        feeds,
        {"processed": {}},
        limit=10,
        now="2026-07-07T12:00:00",
        collected_date="2026-07-07",
        select=lambda feed, state, *, limit: articles,
        extract=_fake_extract,
        summarize=summarize,
    )

    assert [b["summary_result"]["title"] for b in result["batch"]] == ["정상 글"]
    assert "bad1" not in result["state"]["processed"]
    assert "good1" in result["state"]["processed"]
    assert result["report"]["articles"]["failed"] == 1
    assert result["report"]["articles"]["succeeded"] == 1


def test_run_fetch_avoids_filename_collision_with_existing_state_meta():
    feeds = [{"name": "피드A", "url": "http://a"}]
    articles = [_article("new1", title="제목")]
    state = {
        "processed": {
            "old1": {
                "processed_at": "2026-07-06T00:00:00",
                "status": "ok",
                "meta": {
                    "filename": "2026-07-07-제목.md",
                    "title": "제목",
                    "published": "2026-07-07",
                    "collected_date": "2026-07-06",
                    "feed_name": "피드A",
                },
            }
        }
    }

    result = pipeline.run_fetch(
        feeds,
        state,
        limit=10,
        now="2026-07-07T12:00:00",
        collected_date="2026-07-07",
        select=lambda feed, s, *, limit: articles,
        extract=_fake_extract,
        summarize=_fake_summarize,
    )

    new_filename = result["state"]["processed"]["new1"]["meta"]["filename"]
    assert new_filename == "2026-07-07-제목-2.md"
    assert result["batch"][0]["filename"] == "2026-07-07-제목-2.md"
    assert "old1" in result["state"]["processed"]


def test_run_fetch_falls_back_to_collected_date_when_published_missing():
    feeds = [{"name": "피드A", "url": "http://a"}]
    articles = [_article("a1", title="발행일 없음 글", published=None)]

    result = pipeline.run_fetch(
        feeds,
        {"processed": {}},
        limit=10,
        now="2026-07-07T12:00:00",
        collected_date="2026-08-01",
        select=lambda feed, state, *, limit: articles,
        extract=_fake_extract,
        summarize=_fake_summarize,
    )

    meta = result["state"]["processed"]["a1"]["meta"]
    assert meta["published"] == "2026-08-01"
    assert meta["filename"].startswith("2026-08-01-")
    assert result["batch"][0]["filename"].startswith("2026-08-01-")


def test_run_fetch_async_matches_sequential_result():
    feeds = [{"name": "피드A", "url": "http://a"}]
    articles = [_article("a1", title="첫 글"), _article("a2", title="둘째 글")]

    sequential = pipeline.run_fetch(
        feeds,
        {"processed": {}},
        limit=10,
        now="2026-07-07T12:00:00",
        collected_date="2026-07-07",
        select=lambda feed, state, *, limit: articles,
        extract=_fake_extract,
        summarize=_fake_summarize,
    )

    parallel = asyncio.run(
        pipeline.run_fetch_async(
            feeds,
            {"processed": {}},
            limit=10,
            now="2026-07-07T12:00:00",
            collected_date="2026-07-07",
            concurrency=4,
            select=lambda feed, state, *, limit: articles,
            extract=_fake_extract,
            summarize=_fake_summarize_async,
        )
    )

    assert parallel["batch"] == sequential["batch"]
    assert parallel["state"] == sequential["state"]
    assert parallel["report"] == sequential["report"]


def test_run_fetch_async_isolates_summarize_failure():
    feeds = [{"name": "피드A", "url": "http://a"}]
    articles = [_article("bad1", title="요약 실패 글"), _article("good1", title="정상 글")]

    async def summarize(article, body, *, feed_name):
        if article["id"] == "bad1":
            raise summarize_module.SummarizeError("요약 실패")
        return await _fake_summarize_async(article, body, feed_name=feed_name)

    result = asyncio.run(
        pipeline.run_fetch_async(
            feeds,
            {"processed": {}},
            limit=10,
            now="2026-07-07T12:00:00",
            collected_date="2026-07-07",
            concurrency=4,
            select=lambda feed, state, *, limit: articles,
            extract=_fake_extract,
            summarize=summarize,
        )
    )

    assert [b["summary_result"]["title"] for b in result["batch"]] == ["정상 글"]
    assert "bad1" not in result["state"]["processed"]
    assert "good1" in result["state"]["processed"]
    assert result["report"]["articles"]["failed"] == 1
    assert result["report"]["articles"]["failures"] == [
        {"feed": "피드A", "article_id": "bad1", "reason": "요약 실패"}
    ]
    assert result["report"]["articles"]["succeeded"] == 1


def test_run_fetch_async_assigns_filenames_deterministically_by_input_order():
    feeds = [{"name": "피드A", "url": "http://a"}]
    articles = [
        _article("a1", title="같은 제목"),
        _article("a2", title="같은 제목"),
    ]

    result = asyncio.run(
        pipeline.run_fetch_async(
            feeds,
            {"processed": {}},
            limit=10,
            now="2026-07-07T12:00:00",
            collected_date="2026-07-07",
            concurrency=4,
            select=lambda feed, state, *, limit: articles,
            extract=_fake_extract,
            summarize=_fake_summarize_async,
        )
    )

    assert result["state"]["processed"]["a1"]["meta"]["filename"] == "2026-07-07-같은-제목.md"
    assert result["state"]["processed"]["a2"]["meta"]["filename"] == "2026-07-07-같은-제목-2.md"
    assert [b["filename"] for b in result["batch"]] == [
        "2026-07-07-같은-제목.md",
        "2026-07-07-같은-제목-2.md",
    ]


def test_run_fetch_async_skips_feed_on_parse_error_and_continues_other_feeds():
    feeds = [{"name": "깨진피드", "url": "http://broken"}, {"name": "정상피드", "url": "http://ok"}]
    ok_articles = [_article("ok1", title="정상 글")]

    def select(feed, state, *, limit):
        if feed["name"] == "깨진피드":
            raise ingest.FeedParseError("파싱 실패")
        return ok_articles

    result = asyncio.run(
        pipeline.run_fetch_async(
            feeds,
            {"processed": {}},
            limit=10,
            now="2026-07-07T12:00:00",
            collected_date="2026-07-07",
            concurrency=4,
            select=select,
            extract=_fake_extract,
            summarize=_fake_summarize_async,
        )
    )

    assert [b["summary_result"]["title"] for b in result["batch"]] == ["정상 글"]
    assert "ok1" in result["state"]["processed"]
    assert result["report"]["feeds"] == {
        "succeeded": 1,
        "failed": 1,
        "failures": [{"feed": "깨진피드", "reason": "파싱 실패"}],
    }


def test_run_fetch_async_respects_concurrency_limit():
    feeds = [{"name": "피드A", "url": "http://a"}]
    articles = [_article(f"a{i}", title=f"글{i}") for i in range(6)]

    current = 0
    max_seen = 0

    async def summarize(article, body, *, feed_name):
        nonlocal current, max_seen
        current += 1
        max_seen = max(max_seen, current)
        await asyncio.sleep(0.01)
        current -= 1
        return await _fake_summarize_async(article, body, feed_name=feed_name)

    result = asyncio.run(
        pipeline.run_fetch_async(
            feeds,
            {"processed": {}},
            limit=10,
            now="2026-07-07T12:00:00",
            collected_date="2026-07-07",
            concurrency=2,
            select=lambda feed, state, *, limit: articles,
            extract=_fake_extract,
            summarize=summarize,
        )
    )

    assert result["report"]["articles"]["succeeded"] == 6
    assert max_seen <= 2
    assert max_seen >= 2


def test_run_fetch_async_emits_progress_events_via_on_progress_callback():
    feeds = [{"name": "피드A", "url": "http://a"}]
    articles = [_article("bad1", title="요약 실패 글"), _article("good1", title="정상 글")]

    async def summarize(article, body, *, feed_name):
        if article["id"] == "bad1":
            raise summarize_module.SummarizeError("요약 실패")
        return await _fake_summarize_async(article, body, feed_name=feed_name)

    events: list[dict] = []

    async def on_progress(event):
        events.append(event)

    result = asyncio.run(
        pipeline.run_fetch_async(
            feeds,
            {"processed": {}},
            limit=10,
            now="2026-07-07T12:00:00",
            collected_date="2026-07-07",
            concurrency=4,
            select=lambda feed, state, *, limit: articles,
            extract=_fake_extract,
            summarize=summarize,
            on_progress=on_progress,
        )
    )

    assert result["report"]["articles"]["succeeded"] == 1
    assert result["report"]["articles"]["failed"] == 1
    assert {"kind": "feed_started", "feed": "피드A"} in events
    assert events.count({"kind": "article_done", "feed": "피드A"}) == 1
    assert events.count({"kind": "article_failed", "feed": "피드A"}) == 1


def test_run_fetch_async_skips_feed_started_event_for_failed_feed_select():
    feeds = [{"name": "깨진피드", "url": "http://broken"}, {"name": "정상피드", "url": "http://ok"}]
    ok_articles = [_article("ok1", title="정상 글")]

    def select(feed, state, *, limit):
        if feed["name"] == "깨진피드":
            raise ingest.FeedParseError("파싱 실패")
        return ok_articles

    events: list[dict] = []

    async def on_progress(event):
        events.append(event)

    asyncio.run(
        pipeline.run_fetch_async(
            feeds,
            {"processed": {}},
            limit=10,
            now="2026-07-07T12:00:00",
            collected_date="2026-07-07",
            concurrency=4,
            select=select,
            extract=_fake_extract,
            summarize=_fake_summarize_async,
            on_progress=on_progress,
        )
    )

    assert {"kind": "feed_started", "feed": "깨진피드"} not in events
    assert {"kind": "feed_started", "feed": "정상피드"} in events
