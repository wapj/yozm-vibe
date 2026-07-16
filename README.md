# [요즘 바이브 코딩] 루프 엔지니어링 

이 저장소는 도서 **[요즘 바이브 코딩] 루프 엔지니어링 **의 예제 코드를 담고 있습니다.

## 설치

```bash
# uv 설치 (없는 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync
```

## 프로젝트 구조

| 폴더 | 설명 |
|------|------|
| `projects/ch04-horse-racing/` | 4장: 경마 게임 |
| `projects/ch07-nanobanana/` | 7장: 나노바나나 프레젠테이션 |
| `projects/ch08-ai-board/` | 8장: 풀스택 AI 게시판 |
| `projects/ch09-shorts-factory/` | 9장: 쇼츠 자동 생성 |

## 실행

```bash
# 특정 프로젝트 실행
uv run --package ch04-horse-racing python -m horse_racing
```

## 목차

### PART 1: 안티그래비티와 바이브 코딩
- 1장: 에이전트 퍼스트 시대의 개막
- 2장: 안티그래비티 탑승 준비
- 3장: 에디터 뷰 vs 매니저 뷰
- 4장: [프로젝트1] 바이브코딩 맛보기 - 경마 게임 만들기

### PART 2: GitHub 워크플로우 자동화
- 5장: 깃허브 MCP로 이슈 관리하기
- 6장: 제미나이를 활용한 PR 리뷰 자동화

### PART 3: 실전 프로젝트
- 7장: [프로젝트2] 나노바나나 프레젠테이션 자동화
- 8장: [프로젝트3] 풀스택 AI 게시판 (SupaBase)
- 9장: [프로젝트4] 쇼츠 자동 생성 시스템

### PART 4: 고급 활용과 팀 협업
- 10장: 워크플로우와 룰(Rules) 커스터마이징
- 11장: 멀티 에이전트 병렬 작업
