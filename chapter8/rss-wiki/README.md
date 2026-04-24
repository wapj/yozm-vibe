# RSS Wiki

RSS 피드에서 수집한 글을 Claude CLI(`-p` 모드)로 자동 요약·분류하고, 주제별로 누적되는 위키 페이지를 만들어 주는 개인용 웹 도구. 상세 사양은 `docs/PRD.md` 참조.

## 요구 사항

- Python 3.11 이상
- [uv](https://docs.astral.sh/uv/) (패키지 관리 및 실행)
- [Claude CLI](https://docs.claude.com/claude-code) — `claude -p` 가 사용자의 구독 컨텍스트로 동작해야 함

## 설치

```bash
uv sync
```

- 런타임·개발 의존성이 `uv.lock` 기준으로 설치된다.
- DB/로그 파일은 앱 시작 시 `./data/rss-wiki.db`, `./data/logs/rss-wiki.log` 경로로 자동 생성된다 (PRD §14).

## 실행 (PRD §14.2)

### 개발 실행 (reload)

```bash
uv run uvicorn rss_wiki.main:app --host 127.0.0.1 --port 8000 --reload
```

### 프로덕션(로컬) 실행

```bash
uv run uvicorn rss_wiki.main:app --host 127.0.0.1 --port 8000
```

기동하면 다음이 자동 수행된다.

- `db.py` 가 `CREATE TABLE IF NOT EXISTS` 로 스키마를 보장 (별도 마이그레이션 도구 없음)
- APScheduler BackgroundScheduler 가 cron `hour='*', minute=0` 로 수집 잡을 등록
- 브라우저에서 <http://127.0.0.1:8000/> 접속

외부 노출 금지. 반드시 `127.0.0.1` 에만 바인딩한다 (PRD §11).

## 수동 수집 트리거

UI 의 "Fetch now" 버튼 또는 curl:

```bash
curl -X POST http://127.0.0.1:8000/api/fetch
```

- 동시 실행은 전역 `fetch_lock` 으로 막힌다. 이미 돌고 있으면 `409` 를 반환한다.

## 테스트

```bash
uv run pytest -x
```

## 디렉토리 레이아웃 (PRD §14.1)

```
rss-wiki/
├── pyproject.toml
├── uv.lock
├── README.md
├── docs/PRD.md
├── data/                 # 런타임 생성, .gitignore
│   ├── rss-wiki.db
│   └── logs/rss-wiki.log
├── src/rss_wiki/
│   ├── main.py           # FastAPI app entrypoint
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── scheduler.py
│   ├── pipeline/         # fetcher, extractor, llm, summarizer, rebuilder, cycle
│   ├── web/              # routes, templates
│   └── prompts/          # article_summarize.txt, wiki_rebuild.txt
└── tests/
```
