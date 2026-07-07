import json

import pytest

from rss_wiki import store


def test_load_feeds_missing_file_returns_empty_list(tmp_path):
    path = tmp_path / "feeds.json"

    assert store.load_feeds(path) == []


def test_load_state_missing_file_returns_default_structure(tmp_path):
    path = tmp_path / "state.json"

    assert store.load_state(path) == {"processed": {}, "failures": []}


def test_feeds_round_trip(tmp_path):
    path = tmp_path / "feeds.json"
    feeds = [
        {"name": "예제 피드", "url": "https://example.com/rss", "added_at": "2026-07-07T00:00:00Z"},
    ]

    store.save_feeds(feeds, path)

    assert store.load_feeds(path) == feeds


def test_state_round_trip(tmp_path):
    path = tmp_path / "state.json"
    state = {
        "processed": {"https://example.com/a": {"processed_at": "2026-07-07T00:00:00Z", "status": "ok"}},
        "failures": [{"url": "https://example.com/b", "reason": "timeout"}],
    }

    store.save_state(state, path)

    assert store.load_state(path) == state


def test_save_feeds_is_atomic_no_leftover_tmp_file(tmp_path):
    path = tmp_path / "feeds.json"

    store.save_feeds([{"name": "a", "url": "https://a.example", "added_at": "2026-07-07T00:00:00Z"}], path)

    leftover = [p for p in tmp_path.iterdir() if p.name != "feeds.json"]
    assert leftover == []
    assert json.loads(path.read_text(encoding="utf-8"))[0]["name"] == "a"


def test_save_overwrites_existing_file_completely(tmp_path):
    path = tmp_path / "state.json"
    store.save_state({"processed": {"x": {"processed_at": "t", "status": "ok"}}, "failures": []}, path)

    new_state = {"processed": {}, "failures": []}
    store.save_state(new_state, path)

    assert store.load_state(path) == new_state


def test_load_feeds_creates_no_file_as_side_effect(tmp_path):
    path = tmp_path / "feeds.json"

    store.load_feeds(path)

    assert not path.exists()


def test_save_feeds_failure_preserves_original_and_leaves_no_tmp_file(tmp_path):
    path = tmp_path / "feeds.json"
    original = [{"name": "원본", "url": "https://a.example", "added_at": "2026-07-07T00:00:00Z"}]
    store.save_feeds(original, path)

    with pytest.raises(TypeError):
        store.save_feeds([{"bad": {1, 2, 3}}], path)  # set은 JSON 직렬화 불가

    leftover = [p for p in tmp_path.iterdir() if p.name != "feeds.json"]
    assert leftover == []
    assert store.load_feeds(path) == original


def test_save_state_failure_preserves_original_and_leaves_no_tmp_file(tmp_path):
    path = tmp_path / "state.json"
    original = {"processed": {}, "failures": []}
    store.save_state(original, path)

    with pytest.raises(TypeError):
        store.save_state({"processed": {1, 2, 3}, "failures": []}, path)  # set은 JSON 직렬화 불가

    leftover = [p for p in tmp_path.iterdir() if p.name != "state.json"]
    assert leftover == []
    assert store.load_state(path) == original


def test_load_feeds_corrupted_json_raises_store_error(tmp_path):
    path = tmp_path / "feeds.json"
    path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(store.StoreError):
        store.load_feeds(path)


def test_load_state_corrupted_json_raises_store_error(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(store.StoreError):
        store.load_state(path)
