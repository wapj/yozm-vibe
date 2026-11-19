---
name: create-issue
description: 사용자의 버그 리포트, 기능 요청, 개선 요청을 GitHub Issue로 정리하고 gh CLI로 생성합니다. "이슈 만들어줘", "버그 리포트 작성", "기능 요청 이슈" 요청에 사용합니다.
---

# GitHub Issue Creator Skill

## Goal

사용자의 요청을 분석해 적절한 GitHub Issue 제목, 본문, 라벨을 작성합니다.

## Instructions

1. 요청을 `bug`, `feature`, `improvement` 중 하나로 분류합니다.
2. `resources/issue_templates.md`에서 해당 유형의 템플릿을 읽습니다.
3. 사용자가 제공하지 않은 필드는 `TODO: 추가 정보 필요`로 표시합니다.
4. 라벨 후보를 제안하고 `gh label list`로 저장소에 존재하는지 확인합니다.
5. Issue 제목, 본문, 라벨을 사용자에게 보여주고 승인받습니다.
6. 승인 후 `gh issue create --title "<제목>" --body "<본문>" --label "<라벨1>,<라벨2>"`를 실행합니다.

## Constraints

- Issue 본문은 한국어로 작성합니다.
- 외부 저장소에 실제 Issue를 만들기 전 저장소와 계정을 확인합니다.
- 생성 전에는 반드시 사용자의 명시적 승인을 받습니다.
