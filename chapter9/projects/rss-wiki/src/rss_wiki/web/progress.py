"""수집 진행 상태 + 단일 실행 락 (순수 인메모리 계층).

파일 시스템·서버·프로세스에 의존하지 않는다. `run_fetch_async`에 이 트래커를
실제로 주입하는 백그라운드 구동·트리거/폴링 라우트 배선은 T27, 진행 상황
실시간 표시 UI는 T28이다.
"""

from __future__ import annotations

import asyncio


class AlreadyRunningError(Exception):
    """이미 실행 중인 수집이 있는 상태에서 재시작을 시도하면 발생."""


class ProgressTracker:
    """한 번의 수집 실행 진행 상태를 담는다.

    상태 전이는 `idle -> running -> done|error`이다. 백그라운드 태스크(생산자)와
    폴링 라우트(소비자)가 동시에 접근하므로, 상태 갱신·조회는 `asyncio.Lock`으로
    경합 없이 처리한다.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._status = "idle"
        self._feeds: dict[str, dict] = {}
        self._articles = {"done": 0, "failed": 0}
        self._report: dict | None = None
        self._error: str | None = None

    async def begin(self) -> None:
        """단일 실행 락을 획득한다. 이미 `running`이면 중복 실행을 차단한다."""
        async with self._lock:
            if self._status == "running":
                raise AlreadyRunningError("이미 수집이 진행 중입니다.")
            self._status = "running"
            self._feeds = {}
            self._articles = {"done": 0, "failed": 0}
            self._report = None
            self._error = None

    async def note_feed_started(self, feed_name: str) -> None:
        async with self._lock:
            self._feeds.setdefault(feed_name, {})["status"] = "running"

    async def note_article_done(self, feed_name: str) -> None:
        async with self._lock:
            self._feeds.setdefault(feed_name, {})
            self._articles["done"] += 1

    async def note_article_failed(self, feed_name: str) -> None:
        async with self._lock:
            self._feeds.setdefault(feed_name, {})
            self._articles["failed"] += 1

    async def finish(self, report: dict) -> None:
        """리포트를 저장하고 `done`으로 전이한 뒤 락을 해제한다(재-`begin()` 가능)."""
        async with self._lock:
            self._status = "done"
            self._report = report

    async def fail(self, message: str) -> None:
        """`error`로 전이하고 락을 해제한다(재-`begin()` 가능)."""
        async with self._lock:
            self._status = "error"
            self._error = message

    async def snapshot(self) -> dict:
        """폴링 응답용으로 JSON 직렬화 가능한 현재 상태 dict를 반환한다."""
        async with self._lock:
            return {
                "status": self._status,
                "feeds": {name: dict(info) for name, info in self._feeds.items()},
                "articles": dict(self._articles),
                "report": self._report,
                "error": self._error,
            }

    async def handle_event(self, event: dict) -> None:
        """`on_progress` 콜백 이벤트 계약(T27 소비): `run_fetch_async`가 방출할

        `{"kind": "feed_started"|"article_done"|"article_failed", "feed": str}`
        형태의 이벤트를 받아 상태에 반영한다.
        """
        kind = event["kind"]
        feed_name = event["feed"]
        if kind == "feed_started":
            await self.note_feed_started(feed_name)
        elif kind == "article_done":
            await self.note_article_done(feed_name)
        elif kind == "article_failed":
            await self.note_article_failed(feed_name)
        else:
            raise ValueError(f"알 수 없는 진행 이벤트 종류: {kind!r}")
