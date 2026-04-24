"""런타임 의존성 설치 검증 (PRD §4)."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RUNTIME_MODULES = [
    "fastapi",
    "uvicorn",
    "jinja2",
    "pydantic",
    "feedparser",
    "trafilatura",
    "apscheduler",
    "python_multipart",
    "markdown",
]


@pytest.mark.parametrize("module_name", RUNTIME_MODULES)
def test_runtime_module_importable(module_name: str) -> None:
    importlib.import_module(module_name)


def test_pyproject_declares_runtime_dependencies() -> None:
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for package in (
        "fastapi",
        "uvicorn[standard]",
        "jinja2",
        "pydantic",
        "feedparser",
        "trafilatura",
        "apscheduler",
        "python-multipart",
        "markdown",
    ):
        assert package in pyproject, f"missing dependency declaration: {package}"
