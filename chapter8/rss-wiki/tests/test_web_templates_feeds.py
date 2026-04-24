"""base.html + feeds.html Jinja2 템플릿 렌더 검증 (TASKS.md §6 템플릿).

`create_app` 의 기본 `templates_dir` (= `config.TEMPLATES_DIR`) 을 그대로 써서
실제 템플릿 파일이 존재할 때 라우트가 인라인 HTML 대신 템플릿을 렌더하는지 확인한다.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rss_wiki import config, db
from rss_wiki.main import create_app


class _FakeScheduler:
    def __init__(self) -> None:
        self.running = False

    def start(self) -> None:
        self.running = True

    def shutdown(self, wait: bool = True) -> None:
        self.running = False


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "rss.db"
    app = create_app(
        connection_factory=lambda: db.get_connection(db_path),
        scheduler_factory=_FakeScheduler,
        # templates_dir 를 명시적으로 지정하지 않아야 기본 패키지 템플릿을 쓴다.
        start_scheduler=False,
    )
    with TestClient(app) as c:
        c.db_path = db_path  # type: ignore[attr-defined]
        yield c


def test_template_files_exist() -> None:
    """배포 경로에 템플릿이 실제로 존재해야 한다."""
    assert (config.TEMPLATES_DIR / "base.html").exists()
    assert (config.TEMPLATES_DIR / "feeds.html").exists()


def test_base_template_has_common_navigation() -> None:
    base = (config.TEMPLATES_DIR / "base.html").read_text(encoding="utf-8")
    # 공통 네비게이션이 base 에 있어야 자식 템플릿들이 중복 없이 재사용한다.
    assert 'href="/"' in base
    assert 'href="/feeds"' in base
    assert 'href="/search"' in base
    assert 'href="/logs"' in base
    assert 'href="/categories/manage"' in base
    # 자식 템플릿이 주입할 블록
    assert "{% block content %}" in base
    assert "{% block title %}" in base


def test_feeds_template_extends_base() -> None:
    feeds = (config.TEMPLATES_DIR / "feeds.html").read_text(encoding="utf-8")
    assert '{% extends "base.html" %}' in feeds
    assert "{% block content %}" in feeds


def test_feeds_page_renders_template_when_available(client: TestClient) -> None:
    resp = client.get("/feeds")
    assert resp.status_code == 200
    html_text = resp.text
    assert "<title>Feeds — RSS Wiki</title>" in html_text
    # base.html 의 공통 네비게이션이 feeds 페이지에 렌더되어야 한다.
    assert 'href="/feeds"' in html_text
    assert 'href="/search"' in html_text
    # 빈 상태 메시지
    assert "등록된 피드가 없습니다" in html_text


def test_feeds_page_lists_rows_via_template(client: TestClient) -> None:
    client.post(
        "/feeds/add",
        data={"url": "https://a.example/rss", "title": "A Blog"},
        follow_redirects=False,
    )
    client.post(
        "/feeds/add",
        data={"url": "https://b.example/rss"},
        follow_redirects=False,
    )

    resp = client.get("/feeds")
    assert resp.status_code == 200
    html_text = resp.text

    assert "https://a.example/rss" in html_text
    assert "https://b.example/rss" in html_text
    assert "A Blog" in html_text
    # 두 행 모두 data-feed-id 가 들어가야 한다.
    assert html_text.count('data-feed-id="') == 2
    # 활성 상태 배지와 toggle/delete 폼이 함께 렌더됨.
    assert "활성" in html_text
    assert "/toggle" in html_text
    assert "/delete" in html_text


def test_feeds_template_renders_inactive_feed(client: TestClient) -> None:
    client.post(
        "/feeds/add",
        data={"url": "https://off.example/rss"},
        follow_redirects=False,
    )
    conn = sqlite3.connect(client.db_path)  # type: ignore[attr-defined]
    conn.execute("UPDATE feeds SET is_active = 0 WHERE url = ?", ("https://off.example/rss",))
    conn.commit()
    conn.close()

    resp = client.get("/feeds")
    assert resp.status_code == 200
    assert "비활성" in resp.text
    assert "활성화" in resp.text  # 토글 버튼 라벨이 반대 상태로 표시되어야 한다.
