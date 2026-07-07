from rss_wiki import wiki
from rss_wiki.web import render


def _meta(**overrides):
    base = {
        "filename": "2026-07-01-a.md",
        "title": "제목",
        "published": "2026-07-01",
        "collected_date": "2026-07-01",
        "feed_name": "피드A",
    }
    base.update(overrides)
    return base


def test_build_list_viewmodel_latest_sorted_desc_by_published():
    articles = [
        _meta(filename="a.md", published="2026-07-01"),
        _meta(filename="b.md", published="2026-07-03"),
        _meta(filename="c.md", published="2026-07-02"),
    ]

    viewmodel = render.build_list_viewmodel(articles)

    assert [a["filename"] for a in viewmodel["latest"]] == ["b.md", "c.md", "a.md"]


def test_build_list_viewmodel_groups_by_feed_with_slug_matching_wiki_slugify():
    articles = [
        _meta(filename="a.md", feed_name="피드 A"),
        _meta(filename="b.md", feed_name="피드 B"),
        _meta(filename="c.md", feed_name="피드 A"),
    ]

    viewmodel = render.build_list_viewmodel(articles)

    by_feed = {group["feed_name"]: group for group in viewmodel["by_feed"]}
    assert set(by_feed) == {"피드 A", "피드 B"}
    assert by_feed["피드 A"]["slug"] == wiki.slugify("피드 A")
    assert [a["filename"] for a in by_feed["피드 A"]["articles"]] == ["a.md", "c.md"]


def test_build_list_viewmodel_groups_by_collected_date():
    articles = [
        _meta(filename="a.md", collected_date="2026-07-01"),
        _meta(filename="b.md", collected_date="2026-07-02"),
        _meta(filename="c.md", collected_date="2026-07-01"),
    ]

    viewmodel = render.build_list_viewmodel(articles)

    by_date = {group["date"]: group for group in viewmodel["by_date"]}
    assert set(by_date) == {"2026-07-01", "2026-07-02"}
    assert [a["filename"] for a in by_date["2026-07-01"]["articles"]] == ["a.md", "c.md"]


def test_build_list_viewmodel_returns_empty_viewmodel_for_empty_input():
    viewmodel = render.build_list_viewmodel([])

    assert viewmodel == {"latest": [], "by_feed": [], "by_date": []}


def test_render_article_html_converts_title_bullets_and_links():
    markdown_text = (
        "# 제목\n\n"
        "- 첫 번째 포인트\n"
        "- 두 번째 포인트\n\n"
        "원문: [링크](https://example.com/article)\n"
    )

    html = render.render_article_html(markdown_text)

    assert "<h1>제목</h1>" in html
    assert "<ul>" in html
    assert "<li>첫 번째 포인트</li>" in html
    assert '<a href="https://example.com/article">링크</a>' in html


def test_render_article_html_normalizes_legacy_plain_link_line():
    markdown_text = (
        "# 제목\n\n"
        "- 원문 링크: https://example.com/legacy\n"
        "- 발행일: 2026-07-01\n"
    )

    html = render.render_article_html(markdown_text)

    assert '<a href="https://example.com/legacy">https://example.com/legacy</a>' in html


def test_render_article_html_keeps_current_markdown_link_line():
    markdown_text = (
        "# 제목\n\n"
        "- 원문: [https://example.com/current](https://example.com/current)\n"
    )

    html = render.render_article_html(markdown_text)

    assert '<a href="https://example.com/current">https://example.com/current</a>' in html


def test_render_article_html_handles_missing_link_line_without_error():
    markdown_text = "# 제목\n\n- 원문: (링크 없음)\n"

    html = render.render_article_html(markdown_text)

    assert "<a " not in html
    assert "(링크 없음)" in html
