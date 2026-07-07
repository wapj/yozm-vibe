import asyncio
import html
import json
import time

from fastapi.testclient import TestClient

from rss_wiki import feeds as feeds_logic
from rss_wiki import wiki
from rss_wiki.web.app import create_app


def _write_state(path, metas):
    processed = {
        str(i): {"processed_at": "2026-07-01T00:00:00+00:00", "status": "ok", "meta": meta}
        for i, meta in enumerate(metas)
    }
    path.write_text(
        json.dumps({"processed": processed, "failures": []}, ensure_ascii=False),
        encoding="utf-8",
    )


def _meta(**overrides):
    base = {
        "filename": "2026-07-01-a.md",
        "title": "글 A",
        "published": "2026-07-01",
        "collected_date": "2026-07-01",
        "feed_name": "피드 A",
    }
    base.update(overrides)
    return base


def test_root_returns_200_html():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "rss-wiki" in response.text


def test_static_design_tokens_css_is_served():
    client = TestClient(create_app())

    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")


def test_static_theme_js_is_served_as_javascript():
    client = TestClient(create_app())

    response = client.get("/static/theme.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]


def test_dark_theme_selector_present_in_css_and_toggle_present_in_page():
    client = TestClient(create_app())

    css_response = client.get("/static/styles.css")
    page_response = client.get("/")

    assert '[data-theme="dark"]' in css_response.text
    assert 'id="theme-toggle"' in page_response.text


def test_index_lists_articles_in_published_desc_order(tmp_path):
    state_path = tmp_path / "state.json"
    _write_state(
        state_path,
        [
            _meta(filename="a.md", title="글A", published="2026-07-01"),
            _meta(filename="b.md", title="글B", published="2026-07-03"),
            _meta(filename="c.md", title="글C", published="2026-07-02"),
        ],
    )
    client = TestClient(create_app(state_path=state_path, wiki_dir=tmp_path / "wiki"))

    response = client.get("/")

    assert response.status_code == 200
    body = response.text
    assert body.index("글B") < body.index("글C") < body.index("글A")


def test_feed_route_lists_only_matching_feed_articles(tmp_path):
    state_path = tmp_path / "state.json"
    _write_state(
        state_path,
        [
            _meta(filename="a.md", title="A글", feed_name="피드 A"),
            _meta(filename="b.md", title="B글", feed_name="피드 B"),
        ],
    )
    client = TestClient(create_app(state_path=state_path, wiki_dir=tmp_path / "wiki"))

    response = client.get(f"/feeds/{wiki.slugify('피드 A')}")

    assert response.status_code == 200
    assert "A글" in response.text
    assert "B글" not in response.text


def test_daily_route_lists_only_matching_date_articles(tmp_path):
    state_path = tmp_path / "state.json"
    _write_state(
        state_path,
        [
            _meta(filename="a.md", title="A글", collected_date="2026-07-01"),
            _meta(filename="b.md", title="B글", collected_date="2026-07-02"),
        ],
    )
    client = TestClient(create_app(state_path=state_path, wiki_dir=tmp_path / "wiki"))

    response = client.get("/daily/2026-07-01")

    assert response.status_code == 200
    assert "A글" in response.text
    assert "B글" not in response.text


def test_article_route_renders_markdown_html_and_display_meta(tmp_path):
    wiki_dir = tmp_path / "wiki"
    articles_dir = wiki_dir / "articles"
    articles_dir.mkdir(parents=True)
    filename = "2026-07-01-a.md"
    (articles_dir / filename).write_text(
        "# 글 제목\n\n"
        "- 포인트 1\n"
        "- 포인트 2\n\n"
        "원문: [링크](https://example.com/article)\n",
        encoding="utf-8",
    )
    state_path = tmp_path / "state.json"
    _write_state(
        state_path,
        [_meta(filename=filename, title="글 제목", published="2026-07-01", feed_name="피드 A")],
    )
    client = TestClient(create_app(state_path=state_path, wiki_dir=wiki_dir))

    response = client.get(f"/articles/{filename}")

    assert response.status_code == 200
    assert "<h1>글 제목</h1>" in response.text
    assert "<li>포인트 1</li>" in response.text
    assert '<a href="https://example.com/article">링크</a>' in response.text
    assert "2026-07-01" in response.text
    assert "피드 A" in response.text


def test_article_route_renders_clickable_link_for_legacy_plain_link_format(tmp_path):
    wiki_dir = tmp_path / "wiki"
    articles_dir = wiki_dir / "articles"
    articles_dir.mkdir(parents=True)
    filename = "2026-07-01-legacy.md"
    (articles_dir / filename).write_text(
        "# 구식 글\n\n"
        "- 원문 링크: https://example.com/legacy-article\n"
        "- 발행일: 2026-07-01\n"
        "- 피드: 피드 A\n\n"
        "요약 본문\n",
        encoding="utf-8",
    )
    state_path = tmp_path / "state.json"
    _write_state(
        state_path,
        [_meta(filename=filename, title="구식 글", published="2026-07-01", feed_name="피드 A")],
    )
    client = TestClient(create_app(state_path=state_path, wiki_dir=wiki_dir))

    response = client.get(f"/articles/{filename}")

    assert response.status_code == 200
    assert '<a href="https://example.com/legacy-article">' in response.text


def test_article_route_returns_404_for_missing_file(tmp_path):
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", wiki_dir=tmp_path / "wiki")
    )

    response = client.get("/articles/nonexistent.md")

    assert response.status_code == 404
    assert "Traceback" not in response.text


def test_index_shows_empty_state_for_zero_articles(tmp_path):
    state_path = tmp_path / "state.json"
    _write_state(state_path, [])
    client = TestClient(create_app(state_path=state_path, wiki_dir=tmp_path / "wiki"))

    response = client.get("/")

    assert response.status_code == 200
    assert "state-empty" in response.text


def test_index_lists_article_missing_published_without_error(tmp_path):
    state_path = tmp_path / "state.json"
    meta = _meta(filename="a.md", title="발행일 없음")
    del meta["published"]
    _write_state(state_path, [meta])
    client = TestClient(create_app(state_path=state_path, wiki_dir=tmp_path / "wiki"))

    response = client.get("/")

    assert response.status_code == 200
    assert "발행일 없음" in response.text


def test_index_omits_trailing_separator_when_published_missing(tmp_path):
    state_path = tmp_path / "state.json"
    meta = _meta(filename="a.md", title="발행일 없음", feed_name="피드 A")
    del meta["published"]
    _write_state(state_path, [meta])
    client = TestClient(create_app(state_path=state_path, wiki_dir=tmp_path / "wiki"))

    response = client.get("/")

    assert response.status_code == 200
    assert "피드 A ·" not in response.text


def _write_feeds(path, feeds):
    path.write_text(json.dumps(feeds, ensure_ascii=False), encoding="utf-8")


def _fake_validate(url: str) -> dict:
    return {"title": f"제목: {url}"}


def test_feeds_admin_lists_registered_feeds(tmp_path):
    feeds_path = tmp_path / "feeds.json"
    _write_feeds(
        feeds_path,
        [{"name": "피드 A", "url": "https://example.com/a.xml", "added_at": "2026-07-01T00:00:00+00:00"}],
    )
    client = TestClient(create_app(feeds_path=feeds_path, validate=_fake_validate))

    response = client.get("/feeds-admin")

    assert response.status_code == 200
    assert "피드 A" in response.text
    assert "https://example.com/a.xml" in response.text


def test_feeds_admin_shows_empty_state_for_zero_feeds(tmp_path):
    feeds_path = tmp_path / "feeds.json"
    client = TestClient(create_app(feeds_path=feeds_path, validate=_fake_validate))

    response = client.get("/feeds-admin")

    assert response.status_code == 200
    assert "state-empty" in response.text


def test_feeds_admin_add_registers_feed_and_redirects(tmp_path):
    feeds_path = tmp_path / "feeds.json"
    _write_feeds(feeds_path, [])
    client = TestClient(create_app(feeds_path=feeds_path, validate=_fake_validate))

    response = client.post(
        "/feeds-admin/add", data={"url": "https://example.com/new.xml"}, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/feeds-admin"
    saved = json.loads(feeds_path.read_text(encoding="utf-8"))
    assert saved == [
        {
            "name": "제목: https://example.com/new.xml",
            "url": "https://example.com/new.xml",
            "added_at": saved[0]["added_at"],
        }
    ]


def test_feeds_admin_add_duplicate_url_rerenders_with_message_no_traceback(tmp_path):
    feeds_path = tmp_path / "feeds.json"
    existing_url = "https://example.com/dup.xml"
    _write_feeds(
        feeds_path,
        [{"name": "기존 피드", "url": existing_url, "added_at": "2026-07-01T00:00:00+00:00"}],
    )
    client = TestClient(create_app(feeds_path=feeds_path, validate=_fake_validate))

    response = client.post("/feeds-admin/add", data={"url": existing_url})

    assert response.status_code == 400
    assert "Traceback" not in response.text
    assert "이미 등록된 피드" in response.text
    saved = json.loads(feeds_path.read_text(encoding="utf-8"))
    assert len(saved) == 1


def test_feeds_admin_add_invalid_url_rerenders_with_message_no_traceback(tmp_path):
    feeds_path = tmp_path / "feeds.json"
    _write_feeds(feeds_path, [])

    def _rejecting_validate(url: str) -> dict:
        raise feeds_logic.FeedValidationError(f"피드를 파싱할 수 없거나 항목이 없습니다: {url}")

    client = TestClient(create_app(feeds_path=feeds_path, validate=_rejecting_validate))

    response = client.post("/feeds-admin/add", data={"url": "https://example.com/invalid.xml"})

    assert response.status_code == 400
    assert "Traceback" not in response.text
    assert "파싱할 수 없" in response.text
    saved = json.loads(feeds_path.read_text(encoding="utf-8"))
    assert saved == []


def test_feeds_admin_remove_deletes_feed_and_redirects(tmp_path):
    feeds_path = tmp_path / "feeds.json"
    target_url = "https://example.com/remove-me.xml"
    _write_feeds(
        feeds_path,
        [{"name": "삭제 대상", "url": target_url, "added_at": "2026-07-01T00:00:00+00:00"}],
    )
    client = TestClient(create_app(feeds_path=feeds_path, validate=_fake_validate))

    response = client.post("/feeds-admin/remove", data={"target": target_url}, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/feeds-admin"
    saved = json.loads(feeds_path.read_text(encoding="utf-8"))
    assert saved == []


def test_feeds_admin_remove_nonexistent_rerenders_with_message_no_traceback(tmp_path):
    feeds_path = tmp_path / "feeds.json"
    _write_feeds(feeds_path, [])
    client = TestClient(create_app(feeds_path=feeds_path, validate=_fake_validate))

    response = client.post("/feeds-admin/remove", data={"target": "https://example.com/nope.xml"})

    assert response.status_code == 400
    assert "Traceback" not in response.text
    assert "일치하는 피드가 없습니다" in response.text


def test_feeds_admin_add_preserves_url_with_plus_and_percent(tmp_path):
    feeds_path = tmp_path / "feeds.json"
    _write_feeds(feeds_path, [])
    client = TestClient(create_app(feeds_path=feeds_path, validate=_fake_validate))
    url = "https://example.com/feed+news.xml?tag=a%2Bb&label=100%25"

    response = client.post("/feeds-admin/add", data={"url": url}, follow_redirects=False)

    assert response.status_code == 303
    saved = json.loads(feeds_path.read_text(encoding="utf-8"))
    assert saved[0]["url"] == url
    listing = client.get("/feeds-admin")
    assert html.escape(url) in listing.text


def test_static_styles_css_defines_feed_list_info_rule():
    client = TestClient(create_app())

    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert "feed-list__info" in response.text


def _poll_progress_until_finished(client, *, max_tries=200, interval=0.01):
    snapshot = None
    for _ in range(max_tries):
        snapshot = client.get("/fetch/progress").json()
        if snapshot["status"] != "running":
            return snapshot
        time.sleep(interval)
    return snapshot


async def _fake_run_fetch_async_success(feeds, state, *, limit, now, collected_date, concurrency, on_progress=None):
    if on_progress is not None:
        await on_progress({"kind": "feed_started", "feed": "피드 A"})
        await on_progress({"kind": "article_done", "feed": "피드 A"})
    meta = {
        "filename": "2026-07-07-새-글.md",
        "title": "새 글",
        "published": "2026-07-07",
        "collected_date": collected_date,
        "feed_name": "피드 A",
    }
    new_processed = dict(state.get("processed", {}))
    new_processed["new-id"] = {"processed_at": now, "status": "ok", "meta": meta}
    return {
        "batch": [
            {
                "summary_result": {
                    "summary": "요약",
                    "title": "새 글",
                    "link": "https://example.com/new",
                    "published": "2026-07-07",
                    "feed_name": "피드 A",
                },
                "collected_date": collected_date,
                "filename": meta["filename"],
            }
        ],
        "state": {**state, "processed": new_processed},
        "report": {
            "feeds": {"succeeded": 1, "failed": 0, "failures": []},
            "articles": {"succeeded": 1, "failed": 0, "failures": []},
        },
    }


async def _fake_run_fetch_async_slow(feeds, state, *, limit, now, collected_date, concurrency, on_progress=None):
    await asyncio.sleep(0.2)
    return await _fake_run_fetch_async_success(
        feeds, state, limit=limit, now=now, collected_date=collected_date, concurrency=concurrency, on_progress=on_progress
    )


def test_fetch_trigger_runs_in_background_and_progress_reports_done(tmp_path):
    state_path = tmp_path / "state.json"
    wiki_dir = tmp_path / "wiki"
    _write_state(state_path, [])
    client = TestClient(
        create_app(
            state_path=state_path,
            wiki_dir=wiki_dir,
            run_fetch_async=_fake_run_fetch_async_success,
            claude_available=lambda: True,
        )
    )

    trigger_response = client.post("/fetch")

    assert trigger_response.status_code == 200
    assert trigger_response.json()["status"] in ("running", "done")

    snapshot = _poll_progress_until_finished(client)

    assert snapshot["status"] == "done"
    assert snapshot["report"]["articles"]["succeeded"] == 1
    assert snapshot["feeds"]["피드 A"]["status"] == "running"
    assert snapshot["articles"] == {"done": 1, "failed": 0}


def test_fetch_trigger_persists_state_and_regenerates_wiki_index(tmp_path):
    state_path = tmp_path / "state.json"
    wiki_dir = tmp_path / "wiki"
    _write_state(state_path, [])
    client = TestClient(
        create_app(
            state_path=state_path,
            wiki_dir=wiki_dir,
            run_fetch_async=_fake_run_fetch_async_success,
            claude_available=lambda: True,
        )
    )

    client.post("/fetch")
    _poll_progress_until_finished(client)

    saved_state = json.loads(state_path.read_text(encoding="utf-8"))
    assert "new-id" in saved_state["processed"]
    assert (wiki_dir / "index.md").exists()
    assert (wiki_dir / "articles" / "2026-07-07-새-글.md").exists()


def test_fetch_trigger_while_running_is_blocked_without_traceback(tmp_path):
    state_path = tmp_path / "state.json"
    wiki_dir = tmp_path / "wiki"
    _write_state(state_path, [])
    client = TestClient(
        create_app(
            state_path=state_path,
            wiki_dir=wiki_dir,
            run_fetch_async=_fake_run_fetch_async_slow,
            claude_available=lambda: True,
        )
    )

    first = client.post("/fetch")
    second = client.post("/fetch")

    assert first.status_code == 200
    assert second.status_code == 409
    assert "Traceback" not in second.text
    assert "이미" in second.json()["detail"]

    _poll_progress_until_finished(client)


def test_fetch_progress_returns_tracker_snapshot_unmodified(tmp_path):
    state_path = tmp_path / "state.json"
    wiki_dir = tmp_path / "wiki"
    _write_state(state_path, [])
    client = TestClient(
        create_app(
            state_path=state_path,
            wiki_dir=wiki_dir,
            run_fetch_async=_fake_run_fetch_async_success,
            claude_available=lambda: True,
        )
    )

    before = client.get("/fetch/progress").json()
    assert before == {
        "status": "idle",
        "feeds": {},
        "articles": {"done": 0, "failed": 0},
        "report": None,
        "error": None,
    }

    client.post("/fetch")
    snapshot = _poll_progress_until_finished(client)

    assert snapshot["report"] == {
        "feeds": {"succeeded": 1, "failed": 0, "failures": []},
        "articles": {"succeeded": 1, "failed": 0, "failures": []},
    }


def test_fetch_trigger_transitions_to_error_when_claude_unavailable(tmp_path):
    state_path = tmp_path / "state.json"
    wiki_dir = tmp_path / "wiki"
    _write_state(state_path, [])
    client = TestClient(
        create_app(
            state_path=state_path,
            wiki_dir=wiki_dir,
            run_fetch_async=_fake_run_fetch_async_success,
            claude_available=lambda: False,
        )
    )

    client.post("/fetch")
    snapshot = _poll_progress_until_finished(client)

    assert snapshot["status"] == "error"
    assert "claude" in snapshot["error"]


def test_fetch_page_renders_trigger_form_progress_area_and_polling_script(tmp_path):
    client = TestClient(
        create_app(state_path=tmp_path / "state.json", wiki_dir=tmp_path / "wiki")
    )

    response = client.get("/fetch")

    assert response.status_code == 200
    assert '<form id="fetch-trigger-form"' in response.text
    assert 'id="fetch-trigger-button"' in response.text
    assert 'id="fetch-progress"' in response.text
    assert '/static/fetch.js' in response.text

    script_response = client.get("/static/fetch.js")
    assert script_response.status_code == 200


def test_static_fetch_js_is_served_as_javascript():
    client = TestClient(create_app())

    response = client.get("/static/fetch.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]


def test_header_nav_links_to_fetch_page():
    client = TestClient(create_app())

    response = client.get("/")

    assert 'href="/fetch"' in response.text


def test_fetch_trigger_transitions_to_error_when_write_wiki_fails(tmp_path):
    """완료 단계에서 `write_wiki`가 예외를 올리면 트래커가 `error`로 전이하고

    `GET /fetch/progress` 스냅샷에 오류 메시지가 노출됨을 확인한다(REVIEW T27
    메모 2 해소). `wiki_dir` 자리에 파일을 미리 만들어 두면 `write_wiki`의
    `directory.mkdir(parents=True, ...)`이 자연스럽게 실패한다.
    """
    state_path = tmp_path / "state.json"
    wiki_dir = tmp_path / "wiki"
    wiki_dir.write_text("이 경로는 디렉터리가 아니라 파일입니다.", encoding="utf-8")
    _write_state(state_path, [])
    client = TestClient(
        create_app(
            state_path=state_path,
            wiki_dir=wiki_dir,
            run_fetch_async=_fake_run_fetch_async_success,
            claude_available=lambda: True,
        )
    )

    client.post("/fetch")
    snapshot = _poll_progress_until_finished(client)

    assert snapshot["status"] == "error"
    assert snapshot["error"]
