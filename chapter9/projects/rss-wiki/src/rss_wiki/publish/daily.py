from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ArticleCard:
    title: str
    url: str
    summary: str
    tags: Sequence[str] = ()


@dataclass(frozen=True)
class CategorySection:
    name: str
    trend_summary: str
    articles: Sequence[ArticleCard]


@dataclass(frozen=True)
class FailingFeed:
    name: str
    url: str
    consecutive_failures: int


def build_daily_magazine(
    *,
    date: str,
    sections: Sequence[CategorySection],
    failing_feeds: Sequence[FailingFeed] = (),
) -> str:
    if not sections:
        raise ValueError("sections가 비어 있습니다. 빈 매거진은 발행할 수 없습니다.")

    lines: list[str] = []
    lines.append(f"# 일간 매거진 — {date}")
    lines.append("")

    for section in sections:
        lines.append(f"## {section.name}")
        lines.append("")
        for trend_line in section.trend_summary.splitlines():
            lines.append(f"> {trend_line}")
        lines.append("")
        for article in section.articles:
            lines.append(f"### {article.title}")
            lines.append("")
            lines.append(f"[{article.title}]({article.url})")
            lines.append("")
            lines.append(article.summary)
            if article.tags:
                lines.append(" ".join(f"#{tag}" for tag in article.tags))
            lines.append("")

    if failing_feeds:
        lines.append("---")
        lines.append("")
        lines.append("## 장애 피드")
        lines.append("")
        for feed in failing_feeds:
            lines.append(
                f"- {feed.name} ({feed.url}) — 연속 실패 {feed.consecutive_failures}회"
            )
        lines.append("")

    return "\n".join(lines)
