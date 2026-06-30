import json

import pytest

import main


@pytest.fixture
def sample_quotes(tmp_path, monkeypatch):
    quotes = [
        {"text": "성공은 계속하려는 용기다.", "author": "윈스턴 처칠"},
        {"text": "단순함은 궁극의 정교함이다.", "author": "레오나르도 다빈치"},
        {"text": "성공의 비결은 단 한 가지, 잘할 수 있는 일에 광적으로 집중하는 것이다.", "author": "톰 모나건"},
    ]
    quotes_file = tmp_path / "quotes.json"
    quotes_file.write_text(json.dumps(quotes, ensure_ascii=False), encoding="utf-8")
    # QUOTES_FILE만 tmp_path로 바꾸면 _db_path()가 같은 디렉터리의
    # quotes.db를 가리키므로, 테스트별로 격리된 새 DB가 quotes.json을 시드한다.
    monkeypatch.setattr(main, "QUOTES_FILE", quotes_file)
    return quotes


def test_search_quotes_returns_matching_items(sample_quotes):
    results = main.search_quotes("성공")
    assert len(results) == 2
    assert all("성공" in q["text"] for q in results)


def test_search_quotes_single_match(sample_quotes):
    results = main.search_quotes("단순함")
    assert len(results) == 1
    assert results[0]["author"] == "레오나르도 다빈치"


def test_search_quotes_no_match_returns_empty(sample_quotes):
    assert main.search_quotes("존재하지않는키워드") == []


def test_search_quotes_empty_keyword_matches_all(sample_quotes):
    assert len(main.search_quotes("")) == len(sample_quotes)


def test_search_quotes_does_not_match_author(sample_quotes):
    # 키워드는 본문(text)만 검색하며 저자(author)는 검색 대상이 아니다.
    assert main.search_quotes("처칠") == []


def test_add_quote_increases_count(sample_quotes):
    before = len(main.load_quotes())
    message = main.add_quote("새로운 명언입니다.", "테스터")
    after = main.load_quotes()
    assert len(after) == before + 1
    assert after[-1] == {"text": "새로운 명언입니다.", "author": "테스터"}
    assert f"현재 {before + 1}개입니다." in message
