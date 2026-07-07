from rss_wiki import wiki


def test_normalize_date_parses_rfc822_published():
    result = wiki.normalize_date("Tue, 07 Jul 2026 09:00:00 +0000", fallback="2026-01-01")

    assert result == "2026-07-07"


def test_normalize_date_parses_iso8601_published():
    result = wiki.normalize_date("2026-07-07T00:00:00Z", fallback="2026-01-01")

    assert result == "2026-07-07"


def test_normalize_date_falls_back_when_published_missing():
    result = wiki.normalize_date(None, fallback="2026-01-01")

    assert result == "2026-01-01"


def test_normalize_date_falls_back_when_published_unparseable():
    result = wiki.normalize_date("알 수 없는 날짜", fallback="2026-01-01")

    assert result == "2026-01-01"


def test_slugify_converts_title_to_filename_safe_slug():
    assert wiki.slugify("Hello, World! 안녕하세요") == "hello-world-안녕하세요"


def test_slugify_falls_back_when_title_missing():
    assert wiki.slugify(None) == "untitled"
    assert wiki.slugify("!!!") == "untitled"


def test_article_filename_without_collision():
    result = wiki.article_filename("예제 제목", "2026-07-07", existing=set())

    assert result == "2026-07-07-예제-제목.md"


def test_article_filename_appends_suffix_on_collision():
    existing = {"2026-07-07-예제-제목.md"}

    result = wiki.article_filename("예제 제목", "2026-07-07", existing=existing)

    assert result == "2026-07-07-예제-제목-2.md"


def test_article_filename_appends_next_suffix_when_first_suffix_taken():
    existing = {"2026-07-07-예제-제목.md", "2026-07-07-예제-제목-2.md"}

    result = wiki.article_filename("예제 제목", "2026-07-07", existing=existing)

    assert result == "2026-07-07-예제-제목-3.md"


def test_render_article_includes_meta_and_trims_summary_whitespace():
    summary_result = {
        "summary": "\n\n  요약문 내용입니다.  \n\n",
        "title": "원문 제목",
        "link": "https://example.com/article",
        "published": "2026-07-07T00:00:00Z",
        "feed_name": "예제 피드",
    }

    result = wiki.render_article(summary_result, fallback="2026-01-01")

    assert "원문 제목" in result
    assert "https://example.com/article" in result
    assert "2026-07-07" in result
    assert "예제 피드" in result
    assert "요약문 내용입니다." in result
    assert not result.startswith("\n")
    assert result.endswith("요약문 내용입니다.\n")


def test_render_article_normalizes_published_display_to_match_filename_date():
    summary_result = {
        "summary": "요약",
        "title": "원문 제목",
        "link": "https://example.com/article",
        "published": "Tue, 07 Jul 2026 09:00:00 +0000",
        "feed_name": "예제 피드",
    }

    result = wiki.render_article(summary_result, fallback="2026-01-01")

    assert "- 발행일: 2026-07-07\n" in result
    assert "2026-07-07T09:00:00" not in result
    assert "Tue, 07 Jul 2026" not in result


def test_render_article_uses_fallback_when_published_missing():
    summary_result = {
        "summary": "요약",
        "title": "원문 제목",
        "link": "https://example.com/article",
        "published": None,
        "feed_name": "예제 피드",
    }

    result = wiki.render_article(summary_result, fallback="2026-01-01")

    assert "- 발행일: 2026-01-01\n" in result


def test_render_article_asserts_label_value_placement():
    summary_result = {
        "summary": "요약",
        "title": "원문 제목",
        "link": "https://example.com/article",
        "published": "2026-07-07T00:00:00Z",
        "feed_name": "예제 피드",
    }

    result = wiki.render_article(summary_result, fallback="2026-01-01")

    assert "- 원문: [https://example.com/article](https://example.com/article)\n" in result
    assert "- 발행일: 2026-07-07\n" in result
    assert "- 피드: 예제 피드\n" in result


def test_render_article_link_is_clickable_after_markdown_html_conversion():
    from rss_wiki.web.render import render_article_html

    summary_result = {
        "summary": "요약",
        "title": "원문 제목",
        "link": "https://example.com/article",
        "published": "2026-07-07T00:00:00Z",
        "feed_name": "예제 피드",
    }

    result = wiki.render_article(summary_result, fallback="2026-01-01")
    html = render_article_html(result)

    assert '<a href="https://example.com/article">https://example.com/article</a>' in html


def test_render_article_renders_without_error_when_link_missing():
    summary_result = {
        "summary": "요약",
        "title": "원문 제목",
        "link": "",
        "published": "2026-07-07T00:00:00Z",
        "feed_name": "예제 피드",
    }

    result = wiki.render_article(summary_result, fallback="2026-01-01")

    assert "- 원문: (링크 없음)\n" in result


def _sample_articles():
    return [
        {
            "filename": "2026-07-07-첫번째-글.md",
            "title": "첫번째 글",
            "published": "2026-07-07",
            "collected_date": "2026-07-07",
            "feed_name": "피드 A",
        },
        {
            "filename": "2026-07-06-두번째-글.md",
            "title": "두번째 글",
            "published": "2026-07-06",
            "collected_date": "2026-07-07",
            "feed_name": "피드 B",
        },
    ]


def test_render_index_includes_article_links_and_feed_links():
    result = wiki.render_index(_sample_articles())

    assert "[첫번째 글](articles/2026-07-07-첫번째-글.md)" in result
    assert "[두번째 글](articles/2026-07-06-두번째-글.md)" in result
    assert "[피드 A](feeds/피드-a.md)" in result
    assert "[피드 B](feeds/피드-b.md)" in result


def test_render_feed_page_lists_only_that_feed_articles():
    result = wiki.render_feed_page("피드 A", _sample_articles())

    assert "[첫번째 글](../articles/2026-07-07-첫번째-글.md)" in result
    assert "두번째 글" not in result


def test_render_daily_page_lists_articles_by_collected_date():
    articles = _sample_articles() + [
        {
            "filename": "2026-07-05-세번째-글.md",
            "title": "세번째 글",
            "published": "2026-07-05",
            "collected_date": "2026-07-05",
            "feed_name": "피드 A",
        }
    ]

    result = wiki.render_daily_page("2026-07-07", articles)

    assert "[첫번째 글](../articles/2026-07-07-첫번째-글.md)" in result
    assert "[두번째 글](../articles/2026-07-06-두번째-글.md)" in result
    assert "세번째 글" not in result


def _sample_write_wiki_input():
    return [
        {
            "summary_result": {
                "title": "먼저 쓴 글",
                "link": "https://example.com/first",
                "published": "2026-07-05T00:00:00Z",
                "feed_name": "피드 A",
                "summary": "먼저 쓴 글 요약",
            },
            "collected_date": "2026-07-06",
        },
        {
            "summary_result": {
                "title": "나중에 쓴 글",
                "link": "https://example.com/second",
                "published": "2026-07-07T00:00:00Z",
                "feed_name": "피드 B",
                "summary": "나중에 쓴 글 요약",
            },
            "collected_date": "2026-07-07",
        },
    ]


def test_write_wiki_creates_directories_and_index(tmp_path):
    wiki.write_wiki(_sample_write_wiki_input(), wiki_dir=tmp_path)

    assert (tmp_path / "articles").is_dir()
    assert (tmp_path / "feeds").is_dir()
    assert (tmp_path / "daily").is_dir()
    assert (tmp_path / "index.md").exists()


def test_write_wiki_writes_each_article_matching_render_article(tmp_path):
    articles = _sample_write_wiki_input()

    wiki.write_wiki(articles, wiki_dir=tmp_path)

    first = articles[0]
    filename = wiki.article_filename(
        first["summary_result"]["title"],
        wiki.normalize_date(first["summary_result"]["published"], fallback=first["collected_date"]),
        existing=set(),
    )
    written = (tmp_path / "articles" / filename).read_text(encoding="utf-8")
    expected = wiki.render_article(first["summary_result"], fallback=first["collected_date"])

    assert written == expected


def test_write_wiki_index_lists_articles_newest_first(tmp_path):
    wiki.write_wiki(_sample_write_wiki_input(), wiki_dir=tmp_path)

    index = (tmp_path / "index.md").read_text(encoding="utf-8")

    assert index.index("나중에 쓴 글") < index.index("먼저 쓴 글")


def test_write_wiki_feed_and_daily_pages_filter_correctly(tmp_path):
    wiki.write_wiki(_sample_write_wiki_input(), wiki_dir=tmp_path)

    feed_a = (tmp_path / "feeds" / "피드-a.md").read_text(encoding="utf-8")
    assert "먼저 쓴 글" in feed_a
    assert "나중에 쓴 글" not in feed_a

    daily_07_06 = (tmp_path / "daily" / "2026-07-06.md").read_text(encoding="utf-8")
    assert "먼저 쓴 글" in daily_07_06
    assert "나중에 쓴 글" not in daily_07_06


def test_write_wiki_appends_suffix_on_filename_collision_within_batch(tmp_path):
    articles = [
        {
            "summary_result": {
                "title": "같은 제목",
                "link": "https://example.com/a",
                "published": "2026-07-07T00:00:00Z",
                "feed_name": "피드 A",
                "summary": "첫 번째 글 요약",
            },
            "collected_date": "2026-07-07",
        },
        {
            "summary_result": {
                "title": "같은 제목",
                "link": "https://example.com/b",
                "published": "2026-07-07T00:00:00Z",
                "feed_name": "피드 A",
                "summary": "두 번째 글 요약",
            },
            "collected_date": "2026-07-07",
        },
    ]

    wiki.write_wiki(articles, wiki_dir=tmp_path)

    assert (tmp_path / "articles" / "2026-07-07-같은-제목.md").exists()
    assert (tmp_path / "articles" / "2026-07-07-같은-제목-2.md").exists()

    index = (tmp_path / "index.md").read_text(encoding="utf-8")
    assert "articles/2026-07-07-같은-제목.md" in index
    assert "articles/2026-07-07-같은-제목-2.md" in index


def test_write_wiki_uses_preassigned_filename_when_provided(tmp_path):
    articles = [
        {
            "summary_result": {
                "title": "제목",
                "link": "https://example.com/a",
                "published": "2026-07-07T00:00:00Z",
                "feed_name": "피드 A",
                "summary": "요약",
            },
            "collected_date": "2026-07-07",
            "filename": "2026-07-07-제목-9.md",
        }
    ]

    wiki.write_wiki(articles, wiki_dir=tmp_path)

    assert (tmp_path / "articles" / "2026-07-07-제목-9.md").exists()
    index = (tmp_path / "index.md").read_text(encoding="utf-8")
    assert "articles/2026-07-07-제목-9.md" in index


def test_write_wiki_with_all_meta_writes_only_batch_files_but_indexes_full_set(tmp_path):
    batch = [
        {
            "summary_result": {
                "title": "새 글",
                "link": "https://example.com/new",
                "published": "2026-07-07T00:00:00Z",
                "feed_name": "피드 A",
                "summary": "새 글 요약",
            },
            "collected_date": "2026-07-07",
            "filename": "2026-07-07-새-글.md",
        }
    ]
    all_meta = [
        {
            "filename": "2026-07-07-새-글.md",
            "title": "새 글",
            "published": "2026-07-07",
            "collected_date": "2026-07-07",
            "feed_name": "피드 A",
        },
        {
            "filename": "2026-07-01-이전-글.md",
            "title": "이전 글",
            "published": "2026-07-01",
            "collected_date": "2026-07-01",
            "feed_name": "피드 B",
        },
    ]

    wiki.write_wiki(batch, wiki_dir=tmp_path, all_meta=all_meta)

    assert (tmp_path / "articles" / "2026-07-07-새-글.md").exists()
    assert not (tmp_path / "articles" / "2026-07-01-이전-글.md").exists()

    index = (tmp_path / "index.md").read_text(encoding="utf-8")
    assert "새 글" in index
    assert "이전 글" in index
    assert index.index("새 글") < index.index("이전 글")

    feed_b = (tmp_path / "feeds" / "피드-b.md").read_text(encoding="utf-8")
    assert "이전 글" in feed_b
