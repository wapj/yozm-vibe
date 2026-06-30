"""FastAPI 앱 엔트리포인트."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from rss_wiki.config import DB_PATH
from rss_wiki.db import init_db
from rss_wiki.scheduler import create_scheduler
from rss_wiki.web.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = init_db(DB_PATH)
    app.state.db = conn
    scheduler = create_scheduler(conn)
    scheduler.start()
    app.state.scheduler = scheduler
    yield
    scheduler.shutdown(wait=False)
    conn.close()


app = FastAPI(title="RSS Wiki", lifespan=lifespan)
app.include_router(router)
