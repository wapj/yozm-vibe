from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FeedConfig:
    name: str
    url: str


def load_feeds(path: str | Path) -> list[FeedConfig]:
    path = Path(path)
    with path.open("rb") as f:
        data = tomllib.load(f)

    feeds = data.get("feed")
    if not feeds:
        raise ValueError(f"No [[feed]] entries found in {path}")

    result: list[FeedConfig] = []
    for i, entry in enumerate(feeds):
        url = entry.get("url", "").strip()
        if not url:
            raise ValueError(f"feed[{i}] is missing a non-empty 'url' field in {path}")
        name = entry.get("name", "").strip()
        result.append(FeedConfig(name=name, url=url))

    return result
