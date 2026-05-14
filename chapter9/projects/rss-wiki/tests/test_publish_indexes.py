import pytest

from rss_wiki.publish.indexes import IndexEntry, build_index


def _base_entries():
    return [
        IndexEntry(title="제목A", url="https://a.example.com", summary="요약A", published_date="2026-05-05"),
        IndexEntry(title="제목B", url="https://b.example.com", summary="요약B", published_date="2026-05-04"),
    ]


def test_build_index_category_includes_name_and_kind():
    result = build_index(kind="category", name="LLM", entries=_base_entries())
    assert "LLM" in result
    assert "카테고리" in result
    h1_lines = [line for line in result.splitlines() if line.startswith("# ")]
    assert len(h1_lines) >= 1


def test_build_index_tag_includes_name_and_kind():
    result = build_index(kind="tag", name="claude", entries=_base_entries())
    assert "claude" in result
    assert "태그" in result
    assert "카테고리" not in result


def test_build_index_renders_entries():
    result = build_index(kind="category", name="AI", entries=_base_entries())
    assert "제목A" in result
    assert "제목B" in result
    assert "https://a.example.com" in result
    assert "https://b.example.com" in result
    assert "요약A" in result
    assert "요약B" in result
    assert "2026-05-05" in result
    assert "2026-05-04" in result


def test_build_index_preserves_entry_order():
    entries = [
        IndexEntry(title="먼저", url="https://first.example.com", summary="첫 요약", published_date="2026-05-05"),
        IndexEntry(title="나중", url="https://second.example.com", summary="둘째 요약", published_date="2026-05-04"),
    ]
    result = build_index(kind="tag", name="python", entries=entries)
    idx_first = result.index("먼저")
    idx_second = result.index("나중")
    assert idx_first < idx_second


def test_build_index_handles_multiline_summary():
    entries = [
        IndexEntry(
            title="제목X",
            url="https://x.example.com",
            summary="첫줄\n둘째줄\n셋째줄",
            published_date="2026-05-05",
        )
    ]
    result = build_index(kind="category", name="멀티라인", entries=entries)
    assert "첫줄" in result
    assert "둘째줄" in result
    assert "셋째줄" in result


def test_build_index_raises_on_invalid_kind():
    with pytest.raises(ValueError):
        build_index(kind="other", name="테스트", entries=_base_entries())


def test_build_index_raises_on_empty_entries_or_name():
    with pytest.raises(ValueError):
        build_index(kind="category", name="AI", entries=[])
    with pytest.raises(ValueError):
        build_index(kind="category", name="", entries=_base_entries())
    with pytest.raises(ValueError):
        build_index(kind="category", name="   ", entries=_base_entries())
