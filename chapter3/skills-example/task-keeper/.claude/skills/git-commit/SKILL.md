---
name: git-commit
description: Git 변경 사항을 분석해 Conventional Commits 형식의 한국어 커밋 메시지를 작성하고, 사용자가 승인하면 커밋합니다. "커밋해줘", "커밋 메시지 작성", "변경 사항 커밋" 요청에 사용합니다.
---

# Git Commit Skill

## Goal

변경 사항을 분석하여 `<type>[optional scope]: <subject>` 형식의 한국어 커밋 메시지를 작성하고 커밋합니다.

## Allowed Types

- feat: 새로운 기능
- fix: 버그 수정
- docs: 문서 변경
- style: 포매팅, 공백 등 의미 없는 스타일 변경
- refactor: 동작을 바꾸지 않는 구조 개선
- perf: 성능 개선
- test: 테스트 추가 또는 수정
- chore: 빌드, 설정, 보조 도구 변경

## Instructions

1. `git status --short`로 변경 파일을 확인합니다.
2. 이미 스테이징된 변경이 있는지 `git diff --staged --stat`로 확인합니다.
3. 스테이징된 변경이 없으면 어떤 파일을 커밋할지 사용자에게 확인합니다.
4. 커밋 대상이 정해지면 `git diff --staged` 또는 선택 파일 diff를 읽고 변경 의도를 요약합니다.
5. 제목은 `type(scope): 한국어 명령형 요약` 형식으로 50자 이내로 작성합니다.
6. 본문은 무엇을 왜 바꿨는지 1~3문장으로 작성합니다.
7. 최종 커밋 메시지와 실행할 `git commit -m "제목" -m "본문"` 명령을 보여주고, 사용자가 승인한 뒤 실행합니다.

## Constraints

- 커밋 메시지는 한국어로 작성합니다.
- 여러 변경 유형이 섞이면 가장 중요한 변경을 기준으로 type을 정합니다.
- 사용자가 명시하지 않은 파일을 임의로 스테이징하지 않습니다.
- 커밋 전 `git status --short`를 다시 확인합니다.
