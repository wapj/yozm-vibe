# todo CLI

`todos.json`에 영속화하는 할일 관리 CLI입니다. 목록 조작(순수 로직)은 `todo_manager.py`로
분리하여 `pytest`로 단위 테스트합니다.

## 구조

| 파일 | 역할 |
|---|---|
| `main.py` | typer 기반 CLI 입출력(상태별 색상 포함) |
| `todo_manager.py` | 목록 조작 순수 로직 + JSON 영속화 |
| `test_todo.py` | `todo_manager`에 대한 pytest 단위 테스트 |
| `todos.json` | 할일 저장 파일(실행 시 생성) |

## 설치

```bash
uv sync
```

## 사용법

```bash
uv run python main.py add "우유 사기"   # 할일 추가
uv run python main.py list             # 목록 출력
uv run python main.py start 1          # id=1 을 작업중으로 변경
uv run python main.py done 1           # id=1 을 완료 처리
```

`list` 출력의 상태 표시 기호:

- `[]` 미완료(todo)
- `[=]` 작업중(doing)
- `[O]` 완료(done)

## 테스트

```bash
uv run pytest
```
