# RSS Wiki

## 1. 개요

RSS Wiki는 수십 개의 RSS 피드를 자동으로 수집·요약·분류하여 AI 큐레이팅 매거진으로 발행하는 도구입니다.
Claude CLI를 활용해 각 글의 요약·카테고리·태그를 생성하고, 일간·주간·월간 마크다운 매거진과 카테고리/태그 인덱스 페이지를 `output/` 디렉터리에 저장합니다.

---

## 2. 요구사항

- **Python 3.12 이상** (`pyproject.toml` `requires-python = ">=3.12"`)
- **Claude CLI** — `claude` 명령이 PATH에 있고 인증이 완료되어 있어야 합니다 (PRD §10).
  인증이 안 되어 있으면 `claude login` 을 먼저 실행하세요.
- **uv** 권장 (또는 `pip`)

---

## 3. 설치

```bash
git clone <repo>
cd rss-wiki
uv sync
```

또는 pip:

```bash
pip install -e .
```

설치 후 동작 확인:

```bash
rss-wiki --help
```

---

## 4. 피드 설정 (`feeds.toml`)

예시 파일을 복사해서 편집합니다:

```bash
cp feeds.example.toml feeds.toml
```

`feeds.toml` 형식:

```toml
[[feed]]
name = "Hacker News Front Page"
url  = "https://hnrss.org/frontpage"

[[feed]]
name = "Python Insider"
url  = "https://feeds.feedburner.com/PythonInsider"
```

피드 추가·삭제는 이 파일을 직접 편집합니다 (PRD §11).
변경 사항은 다음 `rss-wiki daily` 실행 시 자동 반영됩니다.

---

## 5. 사용법

### 일간 발행

```bash
rss-wiki daily
```

- RSS 피드 수집 → 본문 추출 → LLM 요약/분류 → 일간 매거진 발행 → 인덱스 갱신
- 출력: `output/daily-YYYY-MM-DD.md`
- 금요일이면 주간 매거진도 자동 발행, 그날이 그 달 마지막 금요일이면 월간 매거진도 자동 발행

### 주간 발행 (단독)

```bash
rss-wiki weekly --end-date 2026-05-08
```

- 지정한 날짜 기준 직전 7일(양 끝 포함)의 글로 주간 통합 요약 발행
- 출력: `output/weekly-YYYY-Www.md`
- `--end-date` 생략 시 오늘 날짜 사용

### 월간 발행 (단독)

```bash
rss-wiki monthly --end-date 2026-05-29
```

- 지정한 날짜가 속한 달의 1일부터 지정일까지의 글로 월간 통합 요약 발행
- 출력: `output/monthly-YYYY-MM.md`
- `--end-date` 생략 시 오늘 날짜 사용

### 전역 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--db` | `data/rss-wiki.db` | SQLite 데이터베이스 경로 |
| `--feeds` | `feeds.toml` | 피드 설정 파일 경로 |
| `--output` | `output` | 마크다운 출력 디렉터리 |
| `--llm-timeout` | `300` | Claude CLI 호출 타임아웃(초) |

경로는 모두 현재 작업 디렉터리 기준입니다.
`--llm-timeout` 은 서브커맨드 뒤에도 지정할 수 있습니다. 예: `rss-wiki weekly --llm-timeout 600`

---

## 6. 자동 트리거 동작

`rss-wiki daily` 호출 시 날짜에 따라 추가 발행이 자동으로 수행됩니다 (PRD §5):

| 조건 | 추가 발행 |
|------|-----------|
| 그날이 금요일 | 주간 매거진 (`weekly`) |
| 그날이 그 달 마지막 금요일 | 주간 + 월간 매거진 (`weekly` + `monthly`) |

- 트리거 판정은 `cli.is_friday` / `cli.is_last_friday_of_month` (stdlib `calendar.monthrange` 기반)
- `weekly`·`monthly` 서브커맨드를 단독으로 호출하면 트리거 판정을 우회합니다

---

## 7. 웹 인터페이스

매거진/인덱스 열람과 피드 관리(추가·수정·삭제·토글·실패 리셋)를 위한 로컬 FastAPI 웹 UI를 제공합니다 (PRD §13).

### 시작

```bash
rss-wiki web
```

- 기본 바인딩: `http://127.0.0.1:8765`
- 브라우저에서 위 주소를 열면 매거진 인덱스가 나타납니다.

### 호스트/포트 변경

```bash
rss-wiki web --host 127.0.0.1 --port 9000
```

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--host` | `127.0.0.1` | 바인딩 호스트 |
| `--port` | `8765` | 바인딩 포트 |

### 보안 경고

- 본 도구는 **개인용·로컬 전용**입니다. 인증·CSRF 보호가 없으므로 외부 노출(`0.0.0.0`/공인 IP 바인딩, 리버스 프록시 노출 등)은 PRD §13 범위 외이며 권장하지 않습니다.
- 다중 사용자, 외부 트래픽이 필요한 경우 별도의 인증 레이어를 운영자가 직접 구성해야 합니다.

### 라우트 요약

| 경로 | 용도 |
|------|------|
| `GET /` | 최근 매거진 목록 |
| `GET /magazines` | 일간/주간/월간 매거진 인덱스 |
| `GET /magazines/{id}` | 매거진 단건(마크다운 → HTML) |
| `GET /categories` | 카테고리 인덱스 |
| `GET /categories/{name}` | 카테고리별 글 목록 |
| `GET /tags/{name}` | 태그별 글 목록 |
| `GET /feeds` | 피드 목록(관리 UI) |
| `POST /feeds` | 피드 추가 |
| `GET /feeds/{id}/edit` | 피드 수정 폼 |
| `POST /feeds/{id}` | 피드 수정 적용 |
| `POST /feeds/{id}/delete` | 피드 삭제(스냅샷 보존) |
| `POST /feeds/{id}/toggle` | 활성/비활성 토글 |
| `POST /feeds/{id}/reset` | 연속 실패 카운트 리셋 |
| `GET /healthz` | 헬스체크 |

상세 동작은 PRD §13을 참조하세요.

### 동시 실행

- `rss-wiki daily`(수집·발행 파이프라인)와 `rss-wiki web`은 **별도 프로세스**로 동시에 실행 가능합니다.
- SQLite는 WAL 모드로 활성화되어 있어 한쪽이 쓰는 동안 다른 쪽이 읽을 수 있습니다.

---

## 8. 자동화 등록

### cron (매일 12:00)

```cron
0 12 * * * cd /Users/<user>/rss-wiki && /Users/<user>/.local/bin/uv run rss-wiki daily >> logs/rss-wiki.log 2>&1
```

- `uv` 절대 경로 확인: `which uv`
- `crontab -e` 로 편집합니다
- `logs/` 디렉터리가 없으면 미리 생성하세요: `mkdir -p logs`

### macOS launchd

`~/Library/LaunchAgents/com.user.rss-wiki.plist` 에 저장:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.rss-wiki</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/&lt;user&gt;/.local/bin/uv</string>
        <string>run</string>
        <string>rss-wiki</string>
        <string>daily</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/&lt;user&gt;/rss-wiki</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>12</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/&lt;user&gt;/rss-wiki/logs/rss-wiki.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/&lt;user&gt;/rss-wiki/logs/rss-wiki.err</string>
</dict>
</plist>
```

등록:

```bash
launchctl load ~/Library/LaunchAgents/com.user.rss-wiki.plist
```

---

## 9. 트러블슈팅

### Claude CLI 미인증

`claude` 명령이 인증 프롬프트를 띄우거나 오류를 반환하는 경우:

```bash
claude login
```

인증 절차를 완료한 뒤 다시 실행하세요. API 키 직접 관리는 불필요합니다 (PRD §10).
미인증 상태에서 실행하면 `LLMError` 트레이스백이 터미널에 출력됩니다.

### Claude CLI 타임아웃

주간·월간 통합 요약처럼 프롬프트가 큰 작업은 오래 걸릴 수 있습니다. 기본 타임아웃은 300초이며, 더 늘리려면 다음처럼 실행하세요:

```bash
rss-wiki weekly --end-date 2026-05-08 --llm-timeout 600
```

### `feeds.toml` 미존재

```bash
cp feeds.example.toml feeds.toml
```

복사 후 URL과 이름을 편집하세요.

### SQLite 경로 권한 오류

`--db data/rss-wiki.db` 의 부모 디렉터리(`data/`)는 첫 실행 시 자동 생성됩니다.
디스크 권한이 부족한 경우 `OSError` 트레이스백이 출력됩니다. 경로를 쓰기 가능한 위치로 변경하세요:

```bash
rss-wiki daily --db /tmp/rss-wiki.db
```

### 연속 실패 피드

5회 연속 수집 실패한 피드는 매거진 하단 "장애 피드" 섹션에 표시됩니다 (PRD §9).
해당 피드의 URL이 변경되었거나 서비스가 종료된 경우 `feeds.toml` 에서 수정하거나 제거하세요.

### 빈 분석 결과 (daily 발행 스킵)

미분석 글이 0건이면 일간 매거진 파일이 생성되지 않고 WARNING 로그만 기록됩니다.
인덱스 갱신은 정상 수행됩니다. 자동 트리거(주간/월간)는 별도 기간 데이터를 사용하므로 영향을 받지 않습니다.

### 포트 점유

`rss-wiki web` 실행 시 `OSError: [Errno 48] Address already in use` 오류가 나오면 다른 프로세스가 같은 포트를 사용 중입니다. 다른 포트로 재실행하세요:

```bash
rss-wiki web --port 8766
```

---

## 10. 디렉터리 구조

```
rss-wiki/
├── src/rss_wiki/
│   ├── config.py          # 피드 설정(TOML) 로딩
│   ├── storage/
│   │   ├── schema.sql     # SQLite DDL
│   │   ├── db.py          # 커넥션·초기화
│   │   └── repo.py        # CRUD 함수
│   ├── ingest/
│   │   ├── fetcher.py     # RSS 수집
│   │   ├── extractor.py   # 본문 추출
│   │   ├── dedupe.py      # URL 정규화·중복 판정
│   │   └── failures.py    # 연속 실패 카운터
│   ├── llm/
│   │   ├── client.py      # Claude CLI subprocess 래퍼
│   │   └── prompts.py     # 프롬프트 빌더·파서
│   ├── publish/
│   │   ├── daily.py       # 일간 매거진 빌더
│   │   ├── weekly.py      # 주간 통합 요약 빌더
│   │   ├── monthly.py     # 월간 통합 요약 빌더
│   │   └── indexes.py     # 카테고리/태그 인덱스 빌더
│   ├── pipeline/
│   │   ├── ingest.py      # 수집 결선층
│   │   ├── llm.py         # LLM 분석 결선층
│   │   └── publish.py     # 발행 결선층
│   └── cli.py             # 엔트리포인트 (argparse + 트리거 판정)
├── feeds.example.toml     # 피드 설정 예시
├── feeds.toml             # 실제 피드 목록 (직접 편집)
├── main.py                # python main.py 진입점
└── output/                # 발행된 마크다운
    ├── daily-YYYY-MM-DD.md
    ├── weekly-YYYY-Www.md
    ├── monthly-YYYY-MM.md
    └── index-{kind}-{name}.md
```
