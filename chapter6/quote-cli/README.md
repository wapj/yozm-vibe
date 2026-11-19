# quote-cli

6장 실습용 quote-cli입니다. 4장의 MCP 서버에 검색 기능과 테스트를 더한 결과물이며, 진입점은 `main.py`, 테스트는 `test_main.py`입니다.

서브에이전트 정의는 이 디렉터리가 아니라 `chapter6/.claude/agents/`에 있습니다. 책은 `chapter6`에서 클로드 코드를 실행하고 `@quote-cli/main.py`를 지정합니다.

```bash
cd chapter6/quote-cli
uv sync
uv run pytest -v
```
