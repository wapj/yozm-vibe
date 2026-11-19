---
name: commit-and-pr
description: 현재 변경 사항을 git-commit 스킬 형식으로 커밋한 뒤, 이어서 create-pr 스킬로 Pull Request를 생성합니다. "커밋하고 PR 올려줘", "commit and pr" 요청에 사용합니다.
disable-model-invocation: true
---

# Commit and PR Skill

## Instructions

1. git-commit 스킬의 절차에 따라 변경 사항을 커밋합니다. 커밋 메시지 형식과 승인 단계도 git-commit을 그대로 따릅니다.
2. 커밋이 끝나면 푸시를 하고 create-pr 스킬의 절차에 따라 PR 제목과 본문을 작성합니다.
3. PR 본문에는 관련 이슈를 `Closes #<번호>`로 연결합니다.

## Constraints

- 커밋과 PR 생성은 각각 사용자 승인을 받은 뒤 실행합니다.
- 커밋 메시지와 PR 본문은 한국어로 작성합니다.
- main 브랜치에서 직접 실행하지 않고 작업 브랜치에서 실행합니다.
