from __future__ import annotations

from markdown_it import MarkdownIt


_md = MarkdownIt("commonmark", {"linkify": True})


def render_markdown(text: str) -> str:
    """마크다운 문자열을 HTML로 렌더링."""
    return _md.render(text)
