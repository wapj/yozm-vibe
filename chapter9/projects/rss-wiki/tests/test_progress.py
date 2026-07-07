import asyncio

import pytest

from rss_wiki.web import progress


def test_initial_status_is_idle():
    tracker = progress.ProgressTracker()

    snapshot = asyncio.run(tracker.snapshot())

    assert snapshot["status"] == "idle"


def test_begin_transitions_to_running():
    async def scenario():
        tracker = progress.ProgressTracker()
        await tracker.begin()
        return await tracker.snapshot()

    snapshot = asyncio.run(scenario())

    assert snapshot["status"] == "running"


def test_begin_while_running_raises_and_blocks_duplicate_run():
    async def scenario():
        tracker = progress.ProgressTracker()
        await tracker.begin()
        with pytest.raises(progress.AlreadyRunningError):
            await tracker.begin()

    asyncio.run(scenario())


def test_progress_events_reflected_in_snapshot_counters():
    async def scenario():
        tracker = progress.ProgressTracker()
        await tracker.begin()
        await tracker.handle_event({"kind": "feed_started", "feed": "피드A"})
        await tracker.handle_event({"kind": "article_done", "feed": "피드A"})
        await tracker.handle_event({"kind": "article_done", "feed": "피드A"})
        await tracker.handle_event({"kind": "article_failed", "feed": "피드A"})
        return await tracker.snapshot()

    snapshot = asyncio.run(scenario())

    assert snapshot["feeds"]["피드A"]["status"] == "running"
    assert snapshot["articles"] == {"done": 2, "failed": 1}


def test_handle_event_rejects_unknown_kind():
    async def scenario():
        tracker = progress.ProgressTracker()
        await tracker.begin()
        with pytest.raises(ValueError):
            await tracker.handle_event({"kind": "unknown", "feed": "피드A"})

    asyncio.run(scenario())


def test_finish_transitions_to_done_with_report_and_allows_rebegin():
    report = {
        "feeds": {"succeeded": 1, "failed": 0, "failures": []},
        "articles": {"succeeded": 2, "failed": 1, "failures": []},
    }

    async def scenario():
        tracker = progress.ProgressTracker()
        await tracker.begin()
        await tracker.finish(report)
        after_finish = await tracker.snapshot()

        await tracker.begin()
        after_rebegin = await tracker.snapshot()
        return after_finish, after_rebegin

    after_finish, after_rebegin = asyncio.run(scenario())

    assert after_finish["status"] == "done"
    assert after_finish["report"] == report
    assert after_rebegin["status"] == "running"


def test_finish_resets_previous_run_progress_on_rebegin():
    async def scenario():
        tracker = progress.ProgressTracker()
        await tracker.begin()
        await tracker.handle_event({"kind": "article_done", "feed": "피드A"})
        await tracker.finish({"feeds": {}, "articles": {}})

        await tracker.begin()
        return await tracker.snapshot()

    snapshot = asyncio.run(scenario())

    assert snapshot["feeds"] == {}
    assert snapshot["articles"] == {"done": 0, "failed": 0}


def test_fail_transitions_to_error_with_message():
    async def scenario():
        tracker = progress.ProgressTracker()
        await tracker.begin()
        await tracker.fail("claude 미설치")
        return await tracker.snapshot()

    snapshot = asyncio.run(scenario())

    assert snapshot["status"] == "error"
    assert snapshot["error"] == "claude 미설치"


def test_fail_allows_rebegin():
    async def scenario():
        tracker = progress.ProgressTracker()
        await tracker.begin()
        await tracker.fail("claude 미설치")
        await tracker.begin()
        return await tracker.snapshot()

    snapshot = asyncio.run(scenario())

    assert snapshot["status"] == "running"
