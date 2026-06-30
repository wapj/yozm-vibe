"""todos.json에 영속화하는 todo CLI.

add / list / start / done 네 가지 서브커맨드를 제공합니다.
입출력(상태별 색상 포함)만 담당하고, 목록 조작 로직은 todo_manager에 위임합니다.
"""

import os

import typer

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

app = typer.Typer(help="todos.json에 저장하는 할일 관리 CLI")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "todos.json")

STATUS_COLOR = {
    STATUS_TODO: typer.colors.WHITE,
    STATUS_DOING: typer.colors.YELLOW,
    STATUS_DONE: typer.colors.GREEN,
}


@app.command()
def add(task: str):
    """새 할일을 추가합니다."""
    todos = load_todos(JSON_PATH)
    todo = add_todo(todos, task)
    save_todos(JSON_PATH, todos)
    print(f"추가됨: {todo['task']} (id={todo['id']})")


@app.command("list")
def list_():
    """할일 목록을 상태별 색상으로 출력합니다."""
    todos = load_todos(JSON_PATH)
    if not todos:
        print("할일이 없습니다.")
        return
    for todo in todos:
        status = todo.get("status", STATUS_TODO)
        symbol = status_symbol(status)
        color = STATUS_COLOR.get(status, typer.colors.WHITE)
        typer.secho(f"{todo['id']}. {symbol} {todo['task']}", fg=color)


@app.command()
def start(todo_id: int):
    """지정한 id의 할일을 작업중 상태로 변경합니다."""
    todos = load_todos(JSON_PATH)
    if start_todo(todos, todo_id):
        save_todos(JSON_PATH, todos)
        print(f"작업중으로 변경됨: id={todo_id}")
    else:
        print("해당 ID의 할일이 없습니다.")


@app.command()
def done(todo_id: int):
    """지정한 id의 할일을 완료 처리합니다."""
    todos = load_todos(JSON_PATH)
    if complete_todo(todos, todo_id):
        save_todos(JSON_PATH, todos)
        print(f"완료 처리됨: id={todo_id}")
    else:
        print("해당 ID의 할일이 없습니다.")


if __name__ == "__main__":
    app()
