---
name: apply-pr-review
description: PR 리뷰 코멘트를 확인하고 코드에 반영한 뒤 각 코멘트에 응답합니다. "PR 리뷰 반영해줘", "리뷰 피드백 적용해줘" 등의 요청에 반응합니다.
---
# GitHub PR Feedback Applier Skill
## Instructions
1. 리뷰 코멘트 가져오기: PR의 모든 리뷰 코멘트를 수집합니다.
gh pr view <PR번호> --json reviews,comments
gh api repos/{owner}/{repo}/pulls/<PR번호>/comments

2. 코멘트 분류 및 분석: 전체 코멘트를 먼저 분석한 후 일괄 처리합니다.
   - 수정 요청 → 코드 변경 반영 (사용자 승인 후 적용)
   - 질문 → 코드 컨텍스트 기반 답변 작성
   - 제안 → 적용 여부를 사용자에게 확인
   - 칭찬/확인 → 간결한 감사 응답
3. 코드 수정 반영: 피드백에 맞게 수정하고 diff를 사용자에게 보여줍니다.
4. 커밋: 커밋메시지는 git-commit 스킬의 지침을 따릅니다. 
5. 코멘트 응답 제출: 작성된 응답을 사용자에게 보여주고 승인 후 제출합니다.
gh api repos/{owner}/{repo}/pulls/<PR번호>/comments/<comment_id>/replies -f body="<응답>"
## 응답 가이드
- 무엇을 어떻게 수정했는지 구체적으로 설명할 것
- 동의하지 않는 경우에도 존중하는 톤으로 이유를 설명할 것
- 모든 코멘트에 빠짐없이 응답할 것 (응답 없는 코멘트 금지)

좋은 예: "N+1 문제를 `select_related`로 해결했습니다."
나쁜 예: "수정했습니다." (구체적 설명 없음)
