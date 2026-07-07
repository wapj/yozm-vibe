"""위키 글 조립 로직과 파일 쓰기 통합(T11)."""

from __future__ import annotations

import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

from rss_wiki import config

_SLUG_RE = re.compile(r"[^a-z0-9가-힣]+")


def _parse_rfc822(value: str):
    try:
        return parsedate_to_datetime(value)
    except Exception:
        return None


def _parse_iso8601(value: str):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def normalize_date(published: str | None, *, fallback: str) -> str:
    """RSS 원문 발행일 문자열(RFC822 또는 ISO8601)을 YYYY-MM-DD로 정규화한다.

    발행일이 없거나 파싱에 실패하면 주입된 fallback(수집일)을 그대로 반환한다.
    """
    if published:
        for parser in (_parse_rfc822, _parse_iso8601):
            parsed = parser(published)
            if parsed is not None:
                return parsed.strftime("%Y-%m-%d")
    return fallback


def slugify(title: str | None, *, fallback: str = "untitled") -> str:
    """제목을 파일명 안전한 슬러그로 변환한다. 제목이 없거나 슬러그가 비면 fallback을 쓴다."""
    if title:
        slug = _SLUG_RE.sub("-", title.strip().lower()).strip("-")
        if slug:
            return slug
    return fallback


def article_filename(title: str | None, date: str, *, existing: set[str]) -> str:
    """`YYYY-MM-DD-<슬러그>.md` 파일명을 만들고, existing과 충돌하면 접미사를 붙인다(PRD 4.4)."""
    slug = slugify(title)
    base = f"{date}-{slug}"
    candidate = f"{base}.md"
    if candidate not in existing:
        return candidate

    suffix = 2
    while f"{base}-{suffix}.md" in existing:
        suffix += 1
    return f"{base}-{suffix}.md"


def render_article(summary_result: dict, *, fallback: str) -> str:
    """summarize_article 반환 dict를 개별 글 마크다운 문자열로 조립한다.

    메타(원제·링크·발행일·피드명)를 문서 상단에 배치하고, summary 앞뒤 공백을
    정리한 뒤 본문으로 잇는다(REVIEW T8 이월 해소: summarize._default_run이
    stdout을 후처리 없이 반환하므로 이 시점에서 정리한다).

    표시용 발행일은 `normalize_date`로 정규화해, 발행일 부재·파싱 실패 시
    주입된 `fallback`(수집일)로 대체하고 파일명 날짜(`article_filename`)와
    형식(`YYYY-MM-DD`)을 통일한다(REVIEW T9 이월 해소).
    """
    title = summary_result.get("title") or "(제목 없음)"
    link = summary_result.get("link") or ""
    published = normalize_date(summary_result.get("published"), fallback=fallback)
    feed_name = summary_result.get("feed_name") or ""
    summary = (summary_result.get("summary") or "").strip()

    link_line = f"- 원문: [{link}]({link})\n" if link else "- 원문: (링크 없음)\n"

    return (
        f"# {title}\n\n"
        f"{link_line}"
        f"- 발행일: {published}\n"
        f"- 피드: {feed_name}\n\n"
        f"{summary}\n"
    )


def render_index(articles: list[dict]) -> str:
    """전체 인덱스(index.md)를 조립한다(PRD 4.4).

    각 글 dict는 표시 메타(filename·title·published·collected_date·feed_name)를
    담는다(자체 결정: 인덱스 입력 계약, IMPL 참고). 최신 글 목록(개별 글 파일로의
    상대 링크)과 피드 목록 링크(feeds/<슬러그>.md, feed_name 기준 중복 제거)를
    포함한다.
    """
    lines = ["# RSS 위키 인덱스", "", "## 최신 글", ""]
    for article in articles:
        title = article.get("title") or "(제목 없음)"
        filename = article["filename"]
        published = article.get("published") or ""
        lines.append(f"- [{title}](articles/{filename}) ({published})")

    lines += ["", "## 피드 목록", ""]
    seen_feeds: dict[str, str] = {}
    for article in articles:
        feed_name = article.get("feed_name") or ""
        if feed_name and feed_name not in seen_feeds:
            seen_feeds[feed_name] = slugify(feed_name)
    for feed_name, slug in seen_feeds.items():
        lines.append(f"- [{feed_name}](feeds/{slug}.md)")

    return "\n".join(lines) + "\n"


def render_feed_page(feed_name: str, articles: list[dict]) -> str:
    """피드별 페이지(feeds/<슬러그>.md)를 조립한다(PRD 4.4).

    `articles`는 render_index와 동일한 표시 메타 dict 리스트(전체 글)를 받아
    `feed_name`이 일치하는 글만 걸러 링크로 나열한다.
    """
    lines = [f"# {feed_name}", ""]
    for article in articles:
        if article.get("feed_name") != feed_name:
            continue
        title = article.get("title") or "(제목 없음)"
        filename = article["filename"]
        published = article.get("published") or ""
        lines.append(f"- [{title}](../articles/{filename}) ({published})")

    return "\n".join(lines) + "\n"


def render_daily_page(date: str, articles: list[dict]) -> str:
    """날짜(수집일)별 페이지(daily/YYYY-MM-DD.md)를 조립한다(PRD 4.4).

    `daily/`는 발행일이 아닌 **수집일** 기준이다. `articles`는 render_index와
    동일한 표시 메타 dict 리스트(전체 글)를 받아 `collected_date`가 일치하는
    글만 걸러 링크로 나열한다.
    """
    lines = [f"# {date}", ""]
    for article in articles:
        if article.get("collected_date") != date:
            continue
        title = article.get("title") or "(제목 없음)"
        filename = article["filename"]
        published = article.get("published") or ""
        lines.append(f"- [{title}](../articles/{filename}) ({published})")

    return "\n".join(lines) + "\n"


def write_wiki(
    articles: list[dict],
    *,
    wiki_dir: Path = config.WIKI_DIR,
    all_meta: list[dict] | None = None,
) -> None:
    """전달받은 글들을 실제 `wiki_dir` 트리에 쓴다(개별 글 파일 + index/feeds/daily).

    `articles`의 각 항목은 `{"summary_result": summarize_article 반환 dict,
    "collected_date": "YYYY-MM-DD", "filename": (선택) 배정된 파일명}` 형태다.
    `filename`이 주어지면(예: `pipeline.run_fetch`가 배정해 state에 저장한 값)
    그대로 사용해 개별 글 파일·인덱스 링크가 state와 어긋나지 않게 하고, 없으면
    이전과 동일하게 배치 내 충돌만 피해 새로 배정한다(T11 하위 호환).

    개별 글 파일은 이번 호출로 전달된 `articles`(이번 배치)만 쓴다. 반면
    index/feeds/daily는 `all_meta`가 주어지면 그 누적 표시 메타 전체로
    재생성하고(REVIEW T11·T12 이월 해소, PRD 4.4 "재생성"), `all_meta`가 없으면
    기존과 같이 이번 배치만으로 조립한다(T11 하위 호환). `state.json`은 읽거나
    쓰지 않는다(PRD 5).
    """
    articles_dir = wiki_dir / "articles"
    feeds_dir = wiki_dir / "feeds"
    daily_dir = wiki_dir / "daily"
    for directory in (articles_dir, feeds_dir, daily_dir):
        directory.mkdir(parents=True, exist_ok=True)

    existing_filenames: set[str] = set()
    batch_metas = []
    for article in articles:
        summary_result = article["summary_result"]
        collected_date = article["collected_date"]
        published = normalize_date(summary_result.get("published"), fallback=collected_date)
        filename = article.get("filename") or article_filename(
            summary_result.get("title"), published, existing=existing_filenames
        )
        existing_filenames.add(filename)

        (articles_dir / filename).write_text(
            render_article(summary_result, fallback=collected_date), encoding="utf-8"
        )

        batch_metas.append(
            {
                "filename": filename,
                "title": summary_result.get("title") or "(제목 없음)",
                "published": published,
                "collected_date": collected_date,
                "feed_name": summary_result.get("feed_name") or "",
            }
        )

    display_metas = list(all_meta) if all_meta is not None else batch_metas
    display_metas = sorted(display_metas, key=lambda meta: meta["published"], reverse=True)

    (wiki_dir / "index.md").write_text(render_index(display_metas), encoding="utf-8")

    feed_names = dict.fromkeys(meta["feed_name"] for meta in display_metas if meta["feed_name"])
    for feed_name in feed_names:
        (feeds_dir / f"{slugify(feed_name)}.md").write_text(
            render_feed_page(feed_name, display_metas), encoding="utf-8"
        )

    collected_dates = dict.fromkeys(meta["collected_date"] for meta in display_metas)
    for date in collected_dates:
        (daily_dir / f"{date}.md").write_text(render_daily_page(date, display_metas), encoding="utf-8")
