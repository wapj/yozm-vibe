from __future__ import annotations

import trafilatura
import httpx

from rss_wiki.ingest.fetcher import FeedEntry


class ExtractError(Exception):
    pass


def extract_body(
    entry: FeedEntry,
    *,
    timeout: float = 10.0,
    client: httpx.Client | None = None,
) -> str | None:
    # Decision: pass response.text (str) to trafilatura.extract — trafilatura handles encoding internally
    def _do_extract(c: httpx.Client) -> str | None:
        try:
            response = c.get(entry.url)
            response.raise_for_status()
            result = trafilatura.extract(response.text)
            if result and result.strip():
                return result
        except (httpx.HTTPStatusError, httpx.RequestError):
            pass
        except Exception:
            pass

        if entry.summary:
            return entry.summary
        return None

    if client is None:
        with httpx.Client(timeout=timeout) as c:
            return _do_extract(c)
    else:
        return _do_extract(client)
