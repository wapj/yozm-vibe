from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db import init_db
from app.routers import health
from app.routers import tasks
from app.routers import pomodoros
import app.models  # noqa: F401 — registers all models with Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Todo + Pomodoro API", lifespan=lifespan)

app.include_router(health.router)
app.include_router(tasks.router)
app.include_router(pomodoros.router)
