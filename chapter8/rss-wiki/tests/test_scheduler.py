"""scheduler — APScheduler 등록 + 전역 fetch_lock (PRD §7.1)."""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from apscheduler.triggers.cron import CronTrigger

from rss_wiki import config, db, scheduler
from rss_wiki.pipeline.cycle import CycleResult


# -----------------------------------------------------------------------------
# build_scheduler — cron 등록
# -----------------------------------------------------------------------------


def test_build_scheduler_registers_single_fetch_job():
    sch = scheduler.build_scheduler(job=lambda: None)
    try:
        jobs = sch.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == scheduler.FETCH_JOB_ID
    finally:
        if sch.running:
            sch.shutdown(wait=False)


def test_build_scheduler_uses_hourly_cron_trigger():
    sch = scheduler.build_scheduler(job=lambda: None)
    try:
        job = sch.get_jobs()[0]
        assert isinstance(job.trigger, CronTrigger)

        fields = {f.name: str(f) for f in job.trigger.fields}
        # minute=0 은 매시 정각, hour='*' 은 매 시각.
        assert fields["minute"] == "0"
        assert fields["hour"] == "*"
    finally:
        if sch.running:
            sch.shutdown(wait=False)


def test_build_scheduler_uses_config_values():
    # 운영 상수가 PRD §14 와 일치해야 한다.
    assert config.SCHEDULER_CRON_HOUR == "*"
    assert config.SCHEDULER_CRON_MINUTE == 0


def test_build_scheduler_job_not_running_until_start():
    sch = scheduler.build_scheduler(job=lambda: None)
    try:
        assert sch.running is False
    finally:
        if sch.running:
            sch.shutdown(wait=False)


# -----------------------------------------------------------------------------
# run_fetch_cycle — lock, connection 수명, runner 주입
# -----------------------------------------------------------------------------


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    path = tmp_path / "scheduler.db"
    conn = db.get_connection(path)
    db.init_schema(conn)
    conn.close()
    return path


class _TrackedConnection:
    """close() 호출을 기록하는 sqlite3.Connection 얇은 래퍼."""

    def __init__(self, inner: sqlite3.Connection) -> None:
        self._inner = inner
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1
        self._inner.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


@pytest.mark.asyncio
async def test_run_fetch_cycle_invokes_runner_with_new_connection(tmp_db: Path):
    opened: list[_TrackedConnection] = []

    def factory() -> _TrackedConnection:
        tracked = _TrackedConnection(db.get_connection(tmp_db))
        opened.append(tracked)
        return tracked  # type: ignore[return-value]

    async def runner(conn: Any) -> CycleResult:
        assert conn is opened[-1]
        return CycleResult(feeds_attempted=3, ok_articles=2)

    result = await scheduler.run_fetch_cycle(
        lock=asyncio.Lock(),
        connection_factory=factory,  # type: ignore[arg-type]
        run_cycle_fn=runner,
    )

    assert result.feeds_attempted == 3
    assert result.ok_articles == 2
    assert len(opened) == 1
    assert opened[0].close_calls == 1


@pytest.mark.asyncio
async def test_run_fetch_cycle_closes_connection_on_runner_exception(
    tmp_db: Path,
):
    opened: list[_TrackedConnection] = []

    def factory() -> _TrackedConnection:
        tracked = _TrackedConnection(db.get_connection(tmp_db))
        opened.append(tracked)
        return tracked  # type: ignore[return-value]

    async def runner(conn: Any) -> CycleResult:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await scheduler.run_fetch_cycle(
            lock=asyncio.Lock(),
            connection_factory=factory,  # type: ignore[arg-type]
            run_cycle_fn=runner,
        )

    assert opened[0].close_calls == 1


@pytest.mark.asyncio
async def test_run_fetch_cycle_raises_fetch_busy_when_lock_held(tmp_db: Path):
    held = asyncio.Lock()
    await held.acquire()
    try:

        async def runner(conn: sqlite3.Connection) -> CycleResult:
            pytest.fail("runner 가 호출되면 안 된다")

        with pytest.raises(scheduler.FetchBusyError):
            await scheduler.run_fetch_cycle(
                lock=held,
                connection_factory=lambda: db.get_connection(tmp_db),
                run_cycle_fn=runner,
            )
    finally:
        held.release()


@pytest.mark.asyncio
async def test_run_fetch_cycle_releases_lock_after_success(tmp_db: Path):
    lock = asyncio.Lock()

    async def runner(conn: sqlite3.Connection) -> CycleResult:
        assert lock.locked()  # 실행 중에는 잠겨 있어야 한다.
        return CycleResult()

    await scheduler.run_fetch_cycle(
        lock=lock,
        connection_factory=lambda: db.get_connection(tmp_db),
        run_cycle_fn=runner,
    )

    assert not lock.locked()


@pytest.mark.asyncio
async def test_run_fetch_cycle_releases_lock_after_failure(tmp_db: Path):
    lock = asyncio.Lock()

    async def runner(conn: sqlite3.Connection) -> CycleResult:
        raise RuntimeError("x")

    with pytest.raises(RuntimeError):
        await scheduler.run_fetch_cycle(
            lock=lock,
            connection_factory=lambda: db.get_connection(tmp_db),
            run_cycle_fn=runner,
        )

    assert not lock.locked()


# -----------------------------------------------------------------------------
# 전역 fetch_lock 존재
# -----------------------------------------------------------------------------


def test_module_exposes_global_fetch_lock():
    assert isinstance(scheduler.fetch_lock, asyncio.Lock)
