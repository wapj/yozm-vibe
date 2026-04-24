"""FastAPI 앱 엔트리포인트 (PRD §5, §14.2).

- lifespan 에서 DB 스키마 초기화, APScheduler 를 start 한다.
- Jinja2 템플릿 환경을 `app.state.templates` 에 둬서 이후 라우트들이 공유한다.
- 라우트 정의는 `rss_wiki.web.routes` 모듈에서 include 한다 (카테고리/피드 공통).
- 테스트가 외부 의존을 주입할 수 있도록 `create_app(...)` 팩토리로 구성한다.
- 모듈 수준 `app` 은 `uvicorn rss_wiki.main:app` 명령의 진입점이다.
"""

from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Callable

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from rss_wiki import config, db
from rss_wiki.scheduler import build_scheduler
from rss_wiki.web.routes import router as feed_router


ConnectionFactory = Callable[[], sqlite3.Connection]
InitSchemaFn = Callable[[sqlite3.Connection], None]
SchedulerFactory = Callable[[], BackgroundScheduler]


def create_app(
    *,
    connection_factory: ConnectionFactory = db.get_connection,
    init_schema: InitSchemaFn = db.init_schema,
    scheduler_factory: SchedulerFactory = build_scheduler,
    templates_dir: Path | None = None,
    start_scheduler: bool = True,
) -> FastAPI:
    tpl_dir = templates_dir if templates_dir is not None else config.TEMPLATES_DIR
    templates = Jinja2Templates(directory=str(tpl_dir))

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        conn = connection_factory()
        try:
            init_schema(conn)
        finally:
            conn.close()

        scheduler = scheduler_factory()
        if start_scheduler:
            scheduler.start()
        app.state.scheduler = scheduler
        try:
            yield
        finally:
            if start_scheduler and getattr(scheduler, "running", False):
                scheduler.shutdown(wait=False)

    app = FastAPI(lifespan=lifespan)
    app.state.templates = templates
    app.state.connection_factory = connection_factory

    app.include_router(feed_router)

    return app


app = create_app()
