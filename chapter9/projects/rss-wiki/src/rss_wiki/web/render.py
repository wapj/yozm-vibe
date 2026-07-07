"""웹 열람 화면을 위한 순수 렌더링 로직(T21).

`state.json` 표시 메타 dict 리스트로 목록 뷰모델(최신순·피드별·날짜별)을
구성하고, 개별 글 마크다운을 HTML로 변환한다. 다른 모듈(feeds/ingest/
extract/summarize/wiki)과 동일하게 파일 시스템·네트워크에 접근하지 않는
주입형 순수 함수만 담는다. 라우트·템플릿·CSS 배선은 T22가 담당한다.
"""

from __future__ import annotations

import re

import markdown as _markdown

from rss_wiki.wiki import slugify

_LINK_LINE_RE = re.compile(r"^(- 원문(?: 링크)?: )(https?://\S+)$", re.MULTILINE)


def sort_latest(articles: list[dict]) -> list[dict]:
    """표시 메타 리스트를 published 내림차순으로 정렬한 새 목록을 반환한다."""
    return sorted(articles, key=lambda meta: meta.get("published") or "", reverse=True)


def group_by_feed(articles: list[dict]) -> list[dict]:
    """published 내림차순 글을 feed_name으로 묶는다.

    그룹 슬러그는 `wiki.slugify(feed_name)`을 재사용해 인덱스·피드 페이지
    링크(`feeds/<슬러그>.md`)와 정합을 유지한다.
    """
    groups: dict[str, dict] = {}
    for article in sort_latest(articles):
        feed_name = article.get("feed_name") or ""
        group = groups.setdefault(
            feed_name,
            {"feed_name": feed_name, "slug": slugify(feed_name), "articles": []},
        )
        group["articles"].append(article)
    return list(groups.values())


def group_by_date(articles: list[dict]) -> list[dict]:
    """published 내림차순 글을 collected_date(수집일)로 묶는다."""
    groups: dict[str, dict] = {}
    for article in sort_latest(articles):
        date = article.get("collected_date") or ""
        group = groups.setdefault(date, {"date": date, "articles": []})
        group["articles"].append(article)
    return list(groups.values())


def build_list_viewmodel(articles: list[dict]) -> dict:
    """표시 메타 리스트로 전체 최신순·피드별·날짜별 목록 뷰모델을 구성한다.

    빈 리스트를 입력하면 각 키가 빈 리스트인 뷰모델을 반환한다(T22 빈 목록
    상태 화면 대비).
    """
    return {
        "latest": sort_latest(articles),
        "by_feed": group_by_feed(articles),
        "by_date": group_by_date(articles),
    }


def _normalize_link_line(markdown_text: str) -> str:
    """원문 링크 줄의 평문 URL을 마크다운 링크 문법으로 정규화한다.

    저장된 `wiki/articles/*.md`는 구식(`- 원문 링크: {url}`)과 신규
    (`- 원문: [{url}]({url})`) 형식이 혼재할 수 있다. python-markdown은 bare
    URL을 자동 링크하지 않으므로(REVIEW T23 블로킹 승계), 변환 전에 원문 링크
    줄에 한정해 평문 URL만 마크다운 링크로 치환한다. 이미 마크다운 링크
    형식이거나 링크가 없는 줄(`(링크 없음)`)은 패턴에 매치되지 않아 그대로
    둔다.
    """
    return _LINK_LINE_RE.sub(lambda m: f"{m.group(1)}[{m.group(2)}]({m.group(2)})", markdown_text)


def render_article_html(markdown_text: str) -> str:
    """개별 글 마크다운 문자열을 HTML로 변환한다(`markdown` 라이브러리 채택)."""
    return _markdown.markdown(_normalize_link_line(markdown_text))
