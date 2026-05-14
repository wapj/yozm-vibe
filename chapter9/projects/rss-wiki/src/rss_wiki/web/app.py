from __future__ import annotations

import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Iterator

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from rss_wiki.storage.db import init_db


DEFAULT_DB_PATH = "data/rss-wiki.db"

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    db_path: Path = request.app.state.db_path
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


from rss_wiki.web.routes_magazines import router as magazines_router  # noqa: E402
from rss_wiki.web.routes_feeds import router as feeds_router  # noqa: E402


def create_app(db_path: str | Path | None = None, *, run_init_db: bool = True) -> FastAPI:
    if db_path is None:
        db_path = os.environ.get("RSS_WIKI_DB", DEFAULT_DB_PATH)
    resolved = Path(db_path)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if run_init_db:
            init_db(resolved)
        conn = sqlite3.connect(resolved)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.commit()
        finally:
            conn.close()
        yield

    app = FastAPI(lifespan=lifespan)
    app.state.db_path = resolved
    app.state.templates = templates

    @app.get("/healthz")
    def healthz() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    app.include_router(magazines_router)
    app.include_router(feeds_router)
    app.mount(
        "/static",
        StaticFiles(directory=Path(__file__).parent / "static"),
        name="static",
    )

    return app


app = create_app()
