"""개발 의존성 설치 검증 (TASKS.md 0번 추가 개발 의존성)."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEV_MODULES = [
    "pytest",
    "pytest_asyncio",
    "httpx",
]


@pytest.mark.parametrize("module_name", DEV_MODULES)
def test_dev_module_importable(module_name: str) -> None:
    importlib.import_module(module_name)


def test_pyproject_declares_dev_dependencies() -> None:
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for package in ("pytest", "pytest-asyncio", "httpx"):
        assert package in pyproject, f"missing dev dependency declaration: {package}"
