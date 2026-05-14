from __future__ import annotations

from typing import Sequence

from .daily import FailingFeed
from .weekly import SourceArticle


def build_monthly_magazine(
    *,
    period_label: str,
    summary: str,
    articles: Sequence[SourceArticle],
    failing_feeds: Sequence[FailingFeed] = (),
) -> str:
    if not summary.strip():
        raise ValueError("summary가 비어 있습니다. 빈 통합 요약은 발행할 수 없습니다.")
    if not articles:
        raise ValueError("articles가 비어 있습니다. 출처 없는 통합 요약은 발행할 수 없습니다.")

    lines: list[str] = []
    lines.append(f"# 월간 매거진 — {period_label}")
    lines.append("")

    lines.append("## 통합 요약")
    lines.append("")
    for line in summary.splitlines():
        lines.append(line)
    lines.append("")

    lines.append("## 출처")
    lines.append("")
    for article in articles:
        lines.append(f"- [{article.title}]({article.url})")
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
