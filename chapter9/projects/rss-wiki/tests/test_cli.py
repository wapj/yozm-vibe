import copy

from typer.testing import CliRunner

from rss_wiki import cli, feeds as feeds_logic, pipeline, store, wiki

runner = CliRunner()


def test_add_converts_store_error_to_user_facing_message(monkeypatch):
    monkeypatch.setattr(store, "load_feeds", lambda: (_ for _ in ()).throw(store.StoreError("손상된 feeds 파일")))

    result = runner.invoke(cli.app, ["add", "http://example.com/rss"])

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert "Traceback" not in result.output
    assert "오류" in result.output


def test_add_converts_duplicate_feed_error_to_user_facing_message(monkeypatch):
    monkeypatch.setattr(store, "load_feeds", lambda: [])
    monkeypatch.setattr(
        feeds_logic,
        "add_feed",
        lambda current, url: (_ for _ in ()).throw(feeds_logic.DuplicateFeedError(f"이미 등록된 피드입니다: {url}")),
    )

    result = runner.invoke(cli.app, ["add", "http://example.com/rss"])

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert "Traceback" not in result.output
    assert "오류" in result.output


def test_add_converts_feed_validation_error_to_user_facing_message(monkeypatch):
    monkeypatch.setattr(store, "load_feeds", lambda: [])
    monkeypatch.setattr(
        feeds_logic,
        "add_feed",
        lambda current, url: (_ for _ in ()).throw(feeds_logic.FeedValidationError("피드를 파싱할 수 없습니다")),
    )

    result = runner.invoke(cli.app, ["add", "http://example.com/rss"])

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert "Traceback" not in result.output
    assert "오류" in result.output


def test_remove_converts_feed_not_found_error_to_user_facing_message(monkeypatch):
    monkeypatch.setattr(store, "load_feeds", lambda: [])
    monkeypatch.setattr(
        feeds_logic,
        "remove_feed",
        lambda current, target: (_ for _ in ()).throw(feeds_logic.FeedNotFoundError(f"일치하는 피드가 없습니다: {target}")),
    )

    result = runner.invoke(cli.app, ["remove", "없는피드"])

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert "Traceback" not in result.output
    assert "오류" in result.output


def test_list_converts_store_error_to_user_facing_message(monkeypatch):
    monkeypatch.setattr(store, "load_feeds", lambda: (_ for _ in ()).throw(store.StoreError("손상된 feeds 파일")))

    result = runner.invoke(cli.app, ["list"])

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert "Traceback" not in result.output
    assert "오류" in result.output


def test_fetch_exits_nonzero_with_message_when_claude_missing(monkeypatch):
    monkeypatch.setattr(cli, "_claude_available", lambda: False)

    result = runner.invoke(cli.app, ["fetch"])

    assert result.exit_code != 0
    assert "claude" in result.output.lower()


def _sample_state():
    return {
        "processed": {
            "old1": {
                "processed_at": "2026-07-01T00:00:00+00:00",
                "status": "ok",
                "meta": {
                    "filename": "2026-07-01-이전-글.md",
                    "title": "이전 글",
                    "published": "2026-07-01",
                    "collected_date": "2026-07-01",
                    "feed_name": "피드A",
                },
            }
        }
    }


def _run_fetch_result(*, feeds_succeeded, feeds_failed, articles_succeeded, articles_failed):
    original = _sample_state()
    new_state = copy.deepcopy(original)
    if articles_succeeded:
        new_state["processed"]["new1"] = {
            "processed_at": "2026-07-07T00:00:00+00:00",
            "status": "ok",
            "meta": {
                "filename": "2026-07-07-새-글.md",
                "title": "새 글",
                "published": "2026-07-07",
                "collected_date": "2026-07-07",
                "feed_name": "피드A",
            },
        }
    batch = (
        [
            {
                "summary_result": {
                    "title": "새 글",
                    "link": "https://example.com/new",
                    "published": "2026-07-07T00:00:00Z",
                    "feed_name": "피드A",
                    "summary": "새 글 요약",
                },
                "collected_date": "2026-07-07",
                "filename": "2026-07-07-새-글.md",
            }
        ]
        if articles_succeeded
        else []
    )
    return {
        "batch": batch,
        "state": new_state,
        "report": {
            "feeds": {"succeeded": feeds_succeeded, "failed": feeds_failed, "failures": []},
            "articles": {"succeeded": articles_succeeded, "failed": articles_failed, "failures": []},
        },
    }


def _make_fake_run_fetch_async(fake_result):
    async def fake_run_fetch_async(feeds, state, *, limit, now, collected_date, concurrency):
        return fake_result

    return fake_run_fetch_async


def test_fetch_partial_failure_exits_zero_and_reports_counts(monkeypatch):
    original_state = _sample_state()
    original_snapshot = copy.deepcopy(original_state)
    fake_result = _run_fetch_result(feeds_succeeded=1, feeds_failed=0, articles_succeeded=1, articles_failed=1)

    monkeypatch.setattr(cli, "_claude_available", lambda: True)
    monkeypatch.setattr(store, "load_feeds", lambda: [{"name": "피드A", "url": "http://a", "added_at": "x"}])
    monkeypatch.setattr(store, "load_state", lambda: original_state)

    captured_run_fetch_args = {}

    async def fake_run_fetch_async(feeds, state, *, limit, now, collected_date, concurrency):
        captured_run_fetch_args["feeds"] = feeds
        captured_run_fetch_args["state"] = state
        captured_run_fetch_args["concurrency"] = concurrency
        return fake_result

    monkeypatch.setattr(pipeline, "run_fetch_async", fake_run_fetch_async)

    captured_write_wiki_args = {}

    def fake_write_wiki(batch, *, all_meta=None, **kwargs):
        captured_write_wiki_args["batch"] = batch
        captured_write_wiki_args["all_meta"] = all_meta

    monkeypatch.setattr(wiki, "write_wiki", fake_write_wiki)

    captured_save_state_args = {}

    def fake_save_state(state):
        captured_save_state_args["state"] = state

    monkeypatch.setattr(store, "save_state", fake_save_state)

    result = runner.invoke(cli.app, ["fetch"])

    assert result.exit_code == 0
    assert "성공 1건" in result.output
    assert "실패 1건" in result.output

    assert captured_write_wiki_args["batch"] == fake_result["batch"]
    assert {meta["filename"] for meta in captured_write_wiki_args["all_meta"]} == {
        "2026-07-01-이전-글.md",
        "2026-07-07-새-글.md",
    }
    assert captured_save_state_args["state"] == fake_result["state"]
    assert original_state == original_snapshot
    assert captured_run_fetch_args["concurrency"] == 4


def test_fetch_feed_parsed_but_all_articles_failed_exits_nonzero(monkeypatch):
    fake_result = _run_fetch_result(feeds_succeeded=1, feeds_failed=0, articles_succeeded=0, articles_failed=1)

    monkeypatch.setattr(cli, "_claude_available", lambda: True)
    monkeypatch.setattr(store, "load_feeds", lambda: [{"name": "피드A", "url": "http://a", "added_at": "x"}])
    monkeypatch.setattr(store, "load_state", lambda: _sample_state())
    monkeypatch.setattr(
        pipeline,
        "run_fetch_async",
        _make_fake_run_fetch_async(fake_result),
    )
    monkeypatch.setattr(wiki, "write_wiki", lambda batch, *, all_meta=None, **kwargs: None)
    monkeypatch.setattr(store, "save_state", lambda state: None)

    result = runner.invoke(cli.app, ["fetch"])

    assert result.exit_code != 0


def test_fetch_total_failure_exits_nonzero(monkeypatch):
    fake_result = _run_fetch_result(feeds_succeeded=0, feeds_failed=1, articles_succeeded=0, articles_failed=0)

    monkeypatch.setattr(cli, "_claude_available", lambda: True)
    monkeypatch.setattr(store, "load_feeds", lambda: [{"name": "피드A", "url": "http://a", "added_at": "x"}])
    monkeypatch.setattr(store, "load_state", lambda: _sample_state())
    monkeypatch.setattr(
        pipeline,
        "run_fetch_async",
        _make_fake_run_fetch_async(fake_result),
    )
    monkeypatch.setattr(wiki, "write_wiki", lambda batch, *, all_meta=None, **kwargs: None)
    monkeypatch.setattr(store, "save_state", lambda state: None)

    result = runner.invoke(cli.app, ["fetch"])

    assert result.exit_code != 0


def test_fetch_no_new_articles_exits_zero(monkeypatch):
    fake_result = _run_fetch_result(feeds_succeeded=1, feeds_failed=0, articles_succeeded=0, articles_failed=0)

    monkeypatch.setattr(cli, "_claude_available", lambda: True)
    monkeypatch.setattr(store, "load_feeds", lambda: [{"name": "피드A", "url": "http://a", "added_at": "x"}])
    monkeypatch.setattr(store, "load_state", lambda: _sample_state())
    monkeypatch.setattr(
        pipeline,
        "run_fetch_async",
        _make_fake_run_fetch_async(fake_result),
    )
    monkeypatch.setattr(wiki, "write_wiki", lambda batch, *, all_meta=None, **kwargs: None)
    monkeypatch.setattr(store, "save_state", lambda state: None)

    result = runner.invoke(cli.app, ["fetch"])

    assert result.exit_code == 0


def test_fetch_no_feeds_registered_exits_zero(monkeypatch):
    fake_result = _run_fetch_result(feeds_succeeded=0, feeds_failed=0, articles_succeeded=0, articles_failed=0)

    monkeypatch.setattr(cli, "_claude_available", lambda: True)
    monkeypatch.setattr(store, "load_feeds", lambda: [])
    monkeypatch.setattr(store, "load_state", lambda: _sample_state())
    monkeypatch.setattr(
        pipeline,
        "run_fetch_async",
        _make_fake_run_fetch_async(fake_result),
    )
    monkeypatch.setattr(wiki, "write_wiki", lambda batch, *, all_meta=None, **kwargs: None)
    monkeypatch.setattr(store, "save_state", lambda state: None)

    result = runner.invoke(cli.app, ["fetch"])

    assert result.exit_code == 0


def test_fetch_passes_concurrency_option_to_pipeline(monkeypatch):
    fake_result = _run_fetch_result(feeds_succeeded=1, feeds_failed=0, articles_succeeded=1, articles_failed=0)

    monkeypatch.setattr(cli, "_claude_available", lambda: True)
    monkeypatch.setattr(store, "load_feeds", lambda: [{"name": "피드A", "url": "http://a", "added_at": "x"}])
    monkeypatch.setattr(store, "load_state", lambda: _sample_state())

    captured = {}

    async def fake_run_fetch_async(feeds, state, *, limit, now, collected_date, concurrency):
        captured["concurrency"] = concurrency
        return fake_result

    monkeypatch.setattr(pipeline, "run_fetch_async", fake_run_fetch_async)
    monkeypatch.setattr(wiki, "write_wiki", lambda batch, *, all_meta=None, **kwargs: None)
    monkeypatch.setattr(store, "save_state", lambda state: None)

    result = runner.invoke(cli.app, ["fetch", "--concurrency", "7"])

    assert result.exit_code == 0
    assert captured["concurrency"] == 7


def test_serve_help_shows_host_and_port_options():
    result = runner.invoke(cli.app, ["serve", "--help"])

    assert result.exit_code == 0
    assert "--host" in result.output
    assert "--port" in result.output


def test_help_lists_five_subcommands():
    result = runner.invoke(cli.app, ["--help"])

    assert result.exit_code == 0
    for name in ["add", "remove", "list", "fetch", "serve"]:
        assert name in result.output
