"""todo 목록 조작을 위한 순수 로직과 JSON 영속화 헬퍼.

순수 함수는 리스트를 입력받아 결과를 반환하므로 파일 입출력 없이 테스트할 수 있습니다.
CLI 입출력(색상 등)은 main.py가 담당하고, 이 모듈은 데이터 조작과 저장만 책임집니다.
"""

import json
import os

STATUS_TODO = "todo"
STATUS_DOING = "doing"
STATUS_DONE = "done"

_SYMBOLS = {
    STATUS_TODO: "[]",
    STATUS_DOING: "[=]",
    STATUS_DONE: "[O]",
}


def next_id(todos):
    """다음에 부여할 고유 id를 반환합니다."""
    if not todos:
        return 1
    return max(todo["id"] for todo in todos) + 1


def add_todo(todos, task):
    """새 할일을 todos에 추가하고 추가된 항목을 반환합니다."""
    todo = {"id": next_id(todos), "task": task, "status": STATUS_TODO}
    todos.append(todo)
    return todo


def set_status(todos, todo_id, status):
    """지정한 id의 할일 상태를 변경합니다. 성공 여부를 반환합니다."""
    for todo in todos:
        if todo["id"] == todo_id:
            todo["status"] = status
            return True
    return False


def start_todo(todos, todo_id):
    """지정한 id의 할일을 작업중 상태로 변경합니다. 성공 여부를 반환합니다."""
    return set_status(todos, todo_id, STATUS_DOING)


def complete_todo(todos, todo_id):
    """지정한 id의 할일을 완료 상태로 변경합니다. 성공 여부를 반환합니다."""
    return set_status(todos, todo_id, STATUS_DONE)


def status_symbol(status):
    """상태에 대응하는 표시 기호를 반환합니다 (완료 [O], 작업중 [=], 미완료 [])."""
    return _SYMBOLS.get(status, _SYMBOLS[STATUS_TODO])


def load_todos(path):
    """파일에서 할일 목록을 불러옵니다. 파일 부재나 파싱 오류 시 빈 리스트를 반환합니다."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_todos(path, todos):
    """할일 목록을 JSON 파일에 저장합니다."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)
