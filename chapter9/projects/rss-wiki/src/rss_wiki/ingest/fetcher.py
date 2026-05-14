from __future__ import annotations

from dataclasses import dataclass

import feedparser
import httpx


@dataclass(frozen=True)
class FeedEntry:
    url: str
    title: str | None
    published_at: str | None
    summary: str | None


class FetchError(Exception):
    pass


def fetch_feed(
    url: str,
    *,
    timeout: float = 10.0,
    client: httpx.Client | None = None,
) -> list[FeedEntry]:
    def _do_fetch(c: httpx.Client) -> list[FeedEntry]:
        try:
            response = c.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise FetchError(f"HTTP error fetching {url}: {e}") from e
        except httpx.RequestError as e:
            raise FetchError(f"Network error fetching {url}: {e}") from e

        parsed = feedparser.parse(response.content)
        entries: list[FeedEntry] = []
        for entry in parsed.entries:
            link = entry.get("link")
            if not link:
                continue
            published_at = entry.get("published") or entry.get("updated") or None
            entries.append(
                FeedEntry(
                    url=link,
                    title=entry.get("title") or None,
                    published_at=published_at,
                    summary=entry.get("summary") or None,
                )
            )
        return entries

    if client is None:
        with httpx.Client(timeout=timeout) as c:
            return _do_fetch(c)
    else:
        return _do_fetch(client)
