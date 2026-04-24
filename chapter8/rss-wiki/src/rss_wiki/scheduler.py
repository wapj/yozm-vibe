"""APScheduler 기반 수집 스케줄러 (PRD §7.1, §14).

- 매시 정각(`hour='*', minute=0`)에 `run_cycle` 을 1회 실행한다.
- 전역 `fetch_lock` (asyncio.Lock) 으로 수동 트리거와 스케줄 트리거의 동시 실행을 막는다.
- 스케줄 잡은 BackgroundScheduler 스레드에서 돈다. 실제 사이클은 async 이므로
  `asyncio.run` 으로 새 이벤트 루프를 연다. 수동 트리거는 FastAPI 의 루프에서 직접
  `run_fetch_cycle` 을 await 한다.
"""

from __future__ import annotations

import asyncio
import sqlite3
from typing import Awaitable, Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from rss_wiki import config, db
from rss_wiki.pipeline.cycle import CycleResult, run_cycle


FETCH_JOB_ID = "fetch_cycle"

fetch_lock: asyncio.Lock = asyncio.Lock()


class FetchBusyError(RuntimeError):
    """이미 fetch 사이클이 진행 중일 때 발생."""


ConnectionFactory = Callable[[], sqlite3.Connection]
RunCycleFn = Callable[[sqlite3.Connection], Awaitable[CycleResult]]


async def run_fetch_cycle(
    *,
    lock: asyncio.Lock | None = None,
    connection_factory: ConnectionFactory = db.get_connection,
    run_cycle_fn: RunCycleFn | None = None,
) -> CycleResult:
    """fetch_lock 하에 한 사이클을 실행한다.

    - 이미 잠겨 있으면 `FetchBusyError` 를 발생시킨다 (409 응답용).
    - 연결은 사이클 종료 후 항상 닫는다 (예외 포함).
    """
    active_lock = lock if lock is not None else fetch_lock
    if active_lock.locked():
        raise FetchBusyError("fetch cycle is already running")

    async with active_lock:
        conn = connection_factory()
        try:
            runner = run_cycle_fn if run_cycle_fn is not None else run_cycle
            return await runner(conn)
        finally:
            conn.close()


def build_scheduler(
    *,
    job: Callable[[], None] | None = None,
) -> BackgroundScheduler:
    """cron(hour='*', minute=0) 으로 fetch 잡이 등록된 스케줄러를 반환한다.

    반환된 스케줄러는 아직 start() 되지 않은 상태다. 호출측이 라이프사이클을 관리한다.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        job if job is not None else _run_fetch_cycle_in_new_loop,
        trigger=CronTrigger(
            hour=config.SCHEDULER_CRON_HOUR,
            minute=config.SCHEDULER_CRON_MINUTE,
        ),
        id=FETCH_JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler


def _run_fetch_cycle_in_new_loop() -> None:
    """BackgroundScheduler 스레드에서 호출. 새 이벤트 루프에서 사이클을 돌린다.

    이미 진행 중(FetchBusyError)이면 이번 tick 은 조용히 건너뛴다.
    """
    try:
        asyncio.run(run_fetch_cycle())
    except FetchBusyError:
        return
