# [요즘 AI] 루프 엔지니어링

이 저장소는 도서 **[요즘 AI] 루프 엔지니어링**(2쇄)의 예제 코드를 담고 있습니다. 실습 도구는 클로드 코드입니다.

## 설치

장마다 독립된 파이썬 프로젝트입니다. 해당 디렉터리에서 의존성을 설치합니다.

```bash
# uv 설치 (없는 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 예: 2장
cd chapter2/todo-cli
uv sync
uv run main.py list
```

저장소 루트에서 워크스페이스 멤버를 한 번에 설치하려면 다음을 실행합니다.

```bash
uv sync --all-packages
```

포함되는 멤버는 `chapter2/todo-cli`, `chapter4/quote-cli`, `chapter8/rss-wiki`, `chapter9/harness`, `chapter9/projects/rss-wiki`, `chapter11/llmops_lab`입니다.

같은 패키지 이름을 쓰는 `chapter6/quote-cli`, `chapter8/rss-wiki-goal`과 자체 락 파일을 두는 `chapter10/todo-loop`는 워크스페이스에 넣지 않았습니다. 해당 디렉터리에서 `uv sync`를 실행합니다.

## 장별 경로

| 경로 | 장 | 내용 |
| --- | --- | --- |
| `chapter1/quote-cli/` | 1장 | 명언 출력기. `quote.py`, `quotes.json`, `test_quote.py` |
| `chapter2/todo-cli/` | 2장 | 할 일 관리 CLI. `main.py`, `todo_manager.py`, `CLAUDE.md` |
| `chapter3/skills-example/task-keeper/.claude/skills/` | 3장 | 깃허브 워크플로 스킬. 앱 코드는 [task-keeper](https://github.com/wapj/task-keeper) |
| `chapter4/quote-cli/` | 4장 | 명언 MCP 서버와 훅. `.claude/hooks/`, `.claude/settings.json` |
| `chapter6/quote-cli/` | 6장 | 검색 기능이 포함된 quote-cli |
| `chapter6/.claude/agents/` | 6장 | `code-reviewer`, `test-runner`. 클로드 코드는 `chapter6`에서 실행하고 `@quote-cli/main.py`를 지정 |
| `.claude/workflows/design-impl-verify.js` | 6장 | JSON에서 SQLite로 옮기는 워크플로. 대상 경로는 `chapter6/quote-cli` |
| `chapter8/rss-wiki/` | 8장 | RSS Wiki. 제품 사양서는 `docs/PRD.md` |
| `chapter8/rss-wiki-goal/` | 8장 | `/goal`로 만든 RSS Wiki |
| `chapter9/harness/` | 9장 | 플래너, 생성자, 평가자 오케스트레이터 |
| `chapter9/projects/` | 9장 | 하네스 결과. `rss-wiki`, `horse-racing`, `todo-app` |
| `chapter10/todo-loop/` | 10장 | TODO 처리 루프 |
| `chapter11/llmops_lab/` | 11장 | 고객 문의 답변 도우미와 랭퓨즈 연동 |

5장(컨텍스트 엔지니어링)과 7장(하네스 엔지니어링)은 별도 예제 디렉터리가 없습니다.

3장 스킬의 책 속 경로는 클론한 `task-keeper/.claude/skills/`입니다. 이 저장소에서는 같은 상대 경로를 `chapter3/skills-example/task-keeper/.claude/skills/`에 두었습니다. 앱을 함께 실행할 때는 [task-keeper](https://github.com/wapj/task-keeper)를 따로 클론한 뒤, 이 스킬 디렉터리를 그 저장소의 `.claude/skills/`로 복사합니다.
