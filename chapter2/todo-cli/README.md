# todo-cli

`todos.json`에 할일을 저장하고 관리하는 명령행 도구입니다. [Typer](https://typer.tiangolo.com/) 기반이며, CLI 입출력(`main.py`)과 목록 조작 로직(`todo_manager.py`)을 분리해 두었습니다.

## 요구 사항

- Python 3.11 이상
- [uv](https://docs.astral.sh/uv/) (패키지 관리·실행)

## 설치

```bash
uv sync
```

## 사용법

모든 명령은 `uv run python main.py <서브커맨드>` 형태로 실행합니다.

### 할일 추가

```bash
uv run python main.py add "우유 사기"
# 추가됨: 우유 사기 (id=1)
```

### 목록 보기

상태별 색상과 기호로 출력합니다.

```bash
uv run python main.py list
# 1. [] 우유 사기
```

### 진행중으로 변경

지정한 id의 할일을 작업중(진행중) 상태로 바꿉니다.

```bash
uv run python main.py start 1
# 작업중으로 변경됨: id=1
```

### 완료 처리

```bash
uv run python main.py done 1
# 완료 처리됨: id=1
```

도움말은 다음과 같이 확인합니다.

```bash
uv run python main.py --help
```

## 상태 표시

| 상태 | 값 | 기호 | 색상 |
|---|---|---|---|
| 할 일 | `todo` | `[]` | 흰색 |
| 진행중 | `doing` | `[=]` | 노란색 |
| 완료 | `done` | `[O]` | 초록색 |

## 데이터 저장

할일은 프로젝트 디렉터리의 `todos.json`에 JSON 형식으로 저장됩니다. 각 항목은 `id`, `task`, `status` 필드를 가집니다.

## 테스트

순수 로직(`todo_manager.py`)에 대한 단위 테스트가 있습니다.

```bash
uv run pytest
```
