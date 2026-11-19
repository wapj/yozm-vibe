---
name: review-pr
description: GitHub Pull Request의 diff와 메타데이터를 분석하고 체크리스트 기반으로 코드 품질, 보안, 성능, 테스트 관점의 리뷰를 작성합니다. "PR 리뷰해줘", "#123 PR 검토" 요청에 사용합니다.
---

# PR Review Skill

## Goal

PR의 변경 사항을 체계적으로 분석하여 구체적이고 실행 가능한 리뷰 코멘트를 작성합니다.

## Arguments

- `/review-pr 123`처럼 PR 번호를 전달할 수 있습니다.
- 인자가 없으면 현재 브랜치의 PR을 기준으로 확인합니다.

## Instructions

1. PR 번호가 있으면 `gh pr view $ARGUMENTS --json title,body,files,commits`와 `gh pr diff $ARGUMENTS`를 실행합니다.
2. PR 번호가 없으면 `gh pr view --json title,body,files,commits`와 `gh pr diff`를 실행합니다.
3. `resources/review_checklist.md`를 읽고 리뷰 기준으로 사용합니다.
4. 문제는 `필수`, `권장`, `제안`, `질문` 중 하나로 분류합니다.
5. 각 문제에는 파일, 위치, 이유, 개선 방향을 함께 적습니다.
6. 전체 평가를 요약하고 `comment`, `approve`, `request-changes` 중 하나를 권장합니다.
7. 사용자가 승인한 경우에만 `gh pr review` 명령으로 제출합니다.

## Constraints

- 리뷰는 한국어로 작성합니다.
- 모호한 지적만 남기지 말고 대안을 함께 제시합니다.
- 실제 리뷰 제출 전 사용자의 명시적 승인을 받습니다.
