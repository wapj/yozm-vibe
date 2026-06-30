export const meta = {
  name: 'json-to-sqlite-migration',
  description: 'quote-cli의 데이터 저장소를 JSON에서 SQLite로 마이그레이션',
  phases: [
    { title: 'Design', detail: '현재 코드 분석 및 SQLite 스키마/마이그레이션 설계' },
    { title: 'Implement', detail: 'main.py와 test_main.py를 SQLite 기반으로 수정' },
    { title: 'Verify', detail: '코드 리뷰와 pytest 검증 병렬 수행' },
  ],
}

const DIR = '/Users/gyus/yozm-ai-agentic/chapter6/quote-cli'

const PLAN_SCHEMA = {
  type: 'object',
  properties: {
    schema_sql: { type: 'string', description: 'quotes 테이블 생성 DDL' },
    db_filename: { type: 'string' },
    design_notes: { type: 'string', description: '데이터 계층 함수별 변경 설계와 마이그레이션(시드) 전략' },
  },
  required: ['schema_sql', 'db_filename', 'design_notes'],
}

phase('Design')
const plan = await agent(
  `${DIR}/main.py 와 ${DIR}/test_main.py, ${DIR}/quotes.json 을 읽고, 데이터 저장소를 JSON에서 표준 라이브러리 sqlite3 기반 SQLite로 바꾸는 마이그레이션을 설계하라.

요구사항:
- 표준 라이브러리 sqlite3만 사용(외부 의존성 추가 금지).
- DB 파일은 main.py와 같은 디렉터리에 위치(예: quotes.db). Path(__file__).parent 기준.
- 기존 quotes.json의 데이터를 보존해야 한다: DB가 없거나 비어 있으면 quotes.json을 시드 데이터로 초기 적재(마이그레이션)한다.
- 기존 공개 함수의 시그니처와 반환 형태를 그대로 유지해야 한다:
  * load_quotes() -> list[dict]  (각 dict은 {"text":..., "author":...})
  * search_quotes(keyword) -> list[dict]  (본문 text에 keyword 포함)
  * get_random_quote() MCP tool
  * add_quote(text, author) MCP tool
  * all_quotes() resource (quote://all) -> 전체 목록 JSON 문자열
  * --search CLI 옵션 동작 유지
- 책 예제 코드의 단순하고 일관된 문체 유지(과도한 예외 처리 추가 금지, 주석 번호 스타일 ①②③ 유지).
- test_main.py는 현재 QUOTES_FILE을 monkeypatch한다. SQLite 전환에 맞춰 테스트가 통과하도록 어떻게 바꿀지도 설계에 포함하라.

스키마 DDL, DB 파일명, 함수별 변경 설계 및 시드 전략을 반환하라.`,
  { phase: 'Design', schema: PLAN_SCHEMA }
)

phase('Implement')
await agent(
  `quote-cli의 데이터 저장소를 JSON에서 SQLite(표준 라이브러리 sqlite3)로 마이그레이션하라. 아래 설계를 따르되, 실제 파일을 Edit/Write로 수정하라.

대상 파일:
- ${DIR}/main.py
- ${DIR}/test_main.py

설계 스키마 DDL:
${plan.schema_sql}

DB 파일명: ${plan.db_filename}

설계 노트:
${plan.design_notes}

구현 지침:
- 표준 라이브러리 sqlite3만 사용. 외부 의존성 추가 금지(pyproject.toml 변경 불필요).
- DB 경로는 Path(__file__).parent 기준. main.py에 DB_FILE 상수 도입.
- get_db_connection() 또는 init_db() 등 DB 초기화/연결 헬퍼를 추가하고, DB가 없거나 비어 있으면 기존 quotes.json을 시드로 적재한다(데이터 보존).
- load_quotes(), search_quotes(), get_random_quote(), add_quote(), all_quotes()를 SQLite 기반으로 재작성하되 반환 형태와 시그니처를 유지한다.
  * search_quotes는 SQL LIKE로 본문(text) 부분일치 검색.
  * all_quotes()는 전체 목록을 기존과 동일하게 JSON 문자열로 반환(text/author 키, ensure_ascii=False, indent=2).
- --search CLI 옵션과 main() 흐름은 그대로 유지.
- 책 예제 문체 유지: 간결하게, 주석 번호 스타일 ①②③ 유지, 과도한 try/except 추가 금지.
- test_main.py를 SQLite 전환에 맞게 수정한다. tmp_path에 임시 DB를 만들고 main.DB_FILE을 monkeypatch하는 방식으로, search_quotes의 기존 5개 테스트 의도(다중 매칭, 단일 매칭, 무매칭, 빈 키워드 전체 매칭, 저자 미검색)를 유지하라. 단, 빈 키워드의 경우 SQL LIKE '%%' 동작에 맞춰 전체 매칭이 유지되도록 한다.

수정을 완료하면 변경한 파일과 핵심 변경점을 요약하여 반환하라.`,
  { phase: 'Implement' }
)

phase('Verify')
const [review, test] = await parallel([
  () => agent(
    `${DIR}/main.py 의 SQLite 마이그레이션 변경을 검토하라. 다음을 중심으로 실제 문제만 간결히 보고하라: SQL 인젝션(파라미터 바인딩 사용 여부), 커넥션 누수, 시드/초기화 멱등성(중복 적재 여부), 기존 MCP 도구·리소스·--search CLI 동작 호환성, 반환 형태 일관성. 심각도와 위치(파일:라인)를 포함하라.`,
    { phase: 'Verify', label: 'code-review', agentType: 'code-reviewer' }
  ),
  () => agent(
    `${DIR} 디렉터리에서 \`uv run --with pytest pytest -v\` 를 실행하고 결과를 요약하라. 실패가 있으면 원인을 분석하라. (참고: 이 프로젝트는 pytest를 의존성에 두지 않으므로 반드시 --with pytest 옵션을 사용해야 한다.)`,
    { phase: 'Verify', label: 'pytest', agentType: 'test-runner' }
  ),
])

return { plan, review, test }