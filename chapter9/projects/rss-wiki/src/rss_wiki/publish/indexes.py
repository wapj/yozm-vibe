from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

_VALID_KINDS = {"category", "tag"}


@dataclass(frozen=True)
class IndexEntry:
    title: str
    url: str
    summary: str
    published_date: str  # ISO 형식 권장 (예: "2026-05-05"); 호출자가 포맷 보장


def build_index(
    *,
    kind: str,                      # "category" 또는 "tag"
    name: str,                      # 카테고리 또는 태그 이름
    entries: Sequence[IndexEntry],  # 호출자가 정렬해 전달; 빌더는 순서를 그대로 출력
) -> str:
    if kind not in _VALID_KINDS:
        raise ValueError(f"kind는 'category' 또는 'tag' 이어야 합니다: {kind!r}")
    if not name.strip():
        raise ValueError("name이 비어 있습니다. 빈 이름의 인덱스는 발행할 수 없습니다.")
    if not entries:
        raise ValueError("entries가 비어 있습니다. 빈 인덱스는 발행할 수 없습니다.")

    kind_label = "카테고리" if kind == "category" else "태그"

    lines: list[str] = []
    lines.append(f"# {kind_label} — {name}")
    lines.append("")

    for entry in entries:
        lines.append(f"## {entry.published_date}")
        lines.append("")
        lines.append(f"[{entry.title}]({entry.url})")
        lines.append("")
        if entry.summary.strip():
            for summary_line in entry.summary.splitlines():
                lines.append(summary_line)
            lines.append("")

    return "\n".join(lines)
