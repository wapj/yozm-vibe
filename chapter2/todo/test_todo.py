"""todo_manager 순수 로직에 대한 pytest 단위 테스트."""

from todo_manager import (
    STATUS_DOING,
    STATUS_DONE,
    STATUS_TODO,
    add_todo,
    complete_todo,
    load_todos,
    save_todos,
    start_todo,
    status_symbol,
)


def test_add_assigns_incrementing_id():
    todos = []
    first = add_todo(todos, "우유 사기")
    second = add_todo(todos, "빵 사기")
    assert first["id"] == 1
    assert second["id"] == 2


def test_add_appends_with_defaults():
    todos = []
    todo = add_todo(todos, "청소하기")
    assert len(todos) == 1
    assert todo["task"] == "청소하기"
    assert todo["status"] == STATUS_TODO


def test_start_marks_doing():
    todos = []
    add_todo(todos, "운동하기")
    assert start_todo(todos, 1) is True
    assert todos[0]["status"] == STATUS_DOING


def test_complete_marks_done():
    todos = []
    add_todo(todos, "운동하기")
    assert complete_todo(todos, 1) is True
    assert todos[0]["status"] == STATUS_DONE


def test_status_change_unknown_id_returns_false():
    todos = []
    add_todo(todos, "독서하기")
    assert complete_todo(todos, 999) is False
    assert start_todo(todos, 999) is False
    assert todos[0]["status"] == STATUS_TODO


def test_status_symbol():
    assert status_symbol(STATUS_TODO) == "[]"
    assert status_symbol(STATUS_DOING) == "[=]"
    assert status_symbol(STATUS_DONE) == "[O]"


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "todos.json"
    todos = []
    add_todo(todos, "저장 테스트")
    save_todos(str(path), todos)
    loaded = load_todos(str(path))
    assert loaded == todos
