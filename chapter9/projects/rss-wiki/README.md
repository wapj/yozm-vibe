# rss-wiki

RSS 피드로 수집한 글을 LLM(`claude` CLI)으로 한국어 요약하여 마크다운 위키 형태로
정리해 주는 개인용 도구. CLI와 로컬 웹 UI를 함께 제공한다.

자세한 사양은 `docs/PRD.md`, 개발 이력은 `docs/TASKS.md`·`docs/JOURNAL.md`를 참고한다.
계획된 전체 마일스톤(M1~M12)이 구현 완료된 상태다.

## 요구 사항

- Python 3.12 이상, [uv](https://docs.astral.sh/uv/)
- [Claude Code CLI](https://claude.com/claude-code) (`claude` 명령) — `fetch` 실행 시 요약 생성에 사용

## 사용법

```bash
uv run rss-wiki --help
```

| 명령 | 동작 |
|---|---|
| `rss-wiki add <URL>` | 피드 등록 (피드 유효성 검증 포함) |
| `rss-wiki remove <URL 또는 이름>` | 피드 삭제 |
| `rss-wiki list` | 등록된 피드 목록 출력 |
| `rss-wiki fetch` | 전체 피드에서 새 글 수집 → 요약 → 위키 갱신 |
| `rss-wiki serve` | 로컬 웹 UI 서버 실행 (기본 `127.0.0.1:8000`) |

`fetch` 옵션:

- `--limit` — 피드 최초 수집 시 가져올 글 개수 (기본 10)
- `--concurrency` — 글 요약 동시 실행 개수 (기본 4)

`serve` 옵션:

- `--host` / `--port` — 바인딩할 호스트·포트 (기본 `127.0.0.1` / `8000`)

## 웹 UI

`rss-wiki serve`로 실행하는 로컬 웹 애플리케이션에서 다음 작업을 수행할 수 있다.

- **글 열람**: 전체 최신순·피드별·날짜별 목록과 개별 글 페이지(요약문·핵심 포인트·원문 링크·발행일·피드명)
- **피드 관리**: 피드 등록(유효성 검증 포함)·삭제·목록 조회
- **수집 실행**: 버튼 클릭으로 수집을 실행하고 피드별·글 단위 진행 상황을 실시간으로 표시, 완료 시 성공/실패 리포트 제공 (진행 중 중복 실행 차단)

디자인 토큰 기반의 일관된 스타일, 라이트/다크 테마(시스템 설정 추종 + 수동 전환),
반응형 레이아웃, WCAG AA 대비를 지원한다.

CLI와 웹 UI는 동일한 설정 파일(`feeds.json`)과 상태 파일(`state.json`)을 공유한다.

## 산출물 구조

수집 결과는 `wiki/` 디렉토리에 마크다운으로 저장되며, 웹 UI는 이 파일들을
렌더링하므로 위키 파일과 웹 화면의 내용이 항상 일치한다.

```
wiki/
├── index.md          # 전체 최신순 인덱스
├── articles/         # 글 단위 요약 파일 (YYYY-MM-DD-제목.md)
├── feeds/            # 피드별 인덱스
└── daily/            # 날짜별 인덱스
```

## 테스트

```bash
uv run pytest
```
