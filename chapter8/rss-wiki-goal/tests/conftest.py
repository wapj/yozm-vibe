"""pytest 공통 픽스처."""

import pytest
from fastapi.testclient import TestClient

from rss_wiki.db import init_db


@pytest.fixture
def db(tmp_path):
    """임시 SQLite DB."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    yield conn
    conn.close()


@pytest.fixture
def app(tmp_path):
    """테스트용 FastAPI 앱 (lifespan 없이 수동 DB 주입)."""
    from fastapi import FastAPI
    from rss_wiki.web.routes import router

    db_path = str(tmp_path / "app_test.db")
    conn = init_db(db_path)

    test_app = FastAPI()
    test_app.include_router(router)
    test_app.state.db = conn

    yield test_app
    conn.close()


@pytest.fixture
def client(app):
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
