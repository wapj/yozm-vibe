import json
import os
import tempfile
from pathlib import Path

from rss_wiki import config


class StoreError(Exception):
    """손상된 저장 파일을 읽으려 할 때 발생."""


def _atomic_write(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except BaseException:
        os.unlink(tmp_path)
        raise


def load_feeds(path: Path = config.FEEDS_PATH) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise StoreError(f"손상된 feeds 파일: {path}") from e


def save_feeds(feeds: list[dict], path: Path = config.FEEDS_PATH) -> None:
    _atomic_write(path, feeds)


def load_state(path: Path = config.STATE_PATH) -> dict:
    if not path.exists():
        return {"processed": {}, "failures": []}
    with path.open(encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise StoreError(f"손상된 state 파일: {path}") from e


def save_state(state: dict, path: Path = config.STATE_PATH) -> None:
    _atomic_write(path, state)
