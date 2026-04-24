"""프로젝트 레이아웃 스모크 테스트 (PRD §14.1)."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_package_importable() -> None:
    import rss_wiki  # noqa: F401


def test_required_directories_exist() -> None:
    for relative in ("src/rss_wiki", "tests", "data/logs", "docs"):
        assert (PROJECT_ROOT / relative).is_dir(), f"missing directory: {relative}"


def test_pyproject_declares_package() -> None:
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "rss-wiki"' in pyproject
    assert 'requires-python = ">=3.11"' in pyproject


def test_gitignore_excludes_runtime_artifacts() -> None:
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    for entry in ("data/rss-wiki.db", "data/logs/*.log", "__pycache__/", ".venv/"):
        assert entry in gitignore, f"missing gitignore entry: {entry}"
