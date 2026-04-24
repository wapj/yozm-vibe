"""README.md 가 PRD §14.2 실행 명령을 반영하는지 검증."""

from __future__ import annotations

from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"


@pytest.fixture(scope="module")
def readme_text() -> str:
    assert README_PATH.is_file(), "README.md 가 프로젝트 루트에 없다"
    text = README_PATH.read_text(encoding="utf-8")
    assert text.strip(), "README.md 가 비어 있다"
    return text


def test_readme_has_dev_run_command(readme_text: str) -> None:
    assert (
        "uv run uvicorn rss_wiki.main:app --host 127.0.0.1 --port 8000 --reload"
        in readme_text
    )


def test_readme_has_prod_run_command(readme_text: str) -> None:
    assert (
        "uv run uvicorn rss_wiki.main:app --host 127.0.0.1 --port 8000"
        in readme_text
    )


def test_readme_has_manual_fetch_command(readme_text: str) -> None:
    assert "curl -X POST http://127.0.0.1:8000/api/fetch" in readme_text


def test_readme_mentions_uv_sync(readme_text: str) -> None:
    assert "uv sync" in readme_text


def test_readme_references_prd(readme_text: str) -> None:
    assert "docs/PRD.md" in readme_text
