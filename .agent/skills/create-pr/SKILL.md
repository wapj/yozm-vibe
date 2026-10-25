---
name: create-pr
description: GitHub Pull Request를 생성합니다. 현재 브랜치의 변경사항을 기반으로 PR 제목과 본문을 자동으로 작성합니다. "PR 만들어줘", "풀리퀘스트 생성해줘", "PR 올려줘" 등의 요청에 반응합니다.
---

# GitHub PR Creator Skill

## Goal
현재 브랜치의 커밋 내역과 변경사항을 분석하여 구조화된 Pull Request를 생성합니다.

## Instructions

1. **브랜치 정보 확인**:

git branch --show-current
# 프로젝트의 베이스 브랜치를 확인합니다 (예: main, develop, master 등)
git log <base_branch>..HEAD --oneline

현재 브랜치 이름과 베이스 브랜치 대비 커밋 내역을 확인합니다.

2. **변경사항 분석**:

git diff <base_branch>..HEAD --stat
변경된 파일 목록과 변경량을 파악합니다.

3. **PR 템플릿 참조**: `resources/pr_template.md` 파일에서 PR 본문 템플릿을 읽습니다.

4. **PR 내용 작성**:
- 제목: 브랜치 이름과 커밋 내역을 기반으로 간결하게 작성합니다.
- 본문: 템플릿의 각 섹션을 커밋 내역과 변경사항으로 채웁니다.
- 커밋 메시지가 커밋 컨벤션을 만족하는 형식이면, 이를 활용하여 변경 유형을 분류합니다.
5. **리뷰어 제안**: 변경된 파일의 경로를 기반으로 적절한 리뷰어를 제안합니다 (CODEOWNERS 파일이 있는 경우).

6. **PR 생성**: 작성된 내용을 사용자에게 보여주고, 승인 후 `gh pr create`로 생성합니다.

gh pr create --title "<제목>" --body "<본문>" --base <base_branch>

## Constraints
- 베이스 브랜치(예: main, develop)에서 작업중이라면 새로운 브랜치를 만들어서 작업 내용을 분리합니다. 
- 이미 해당 브랜치로 열려있는 PR이 있는지 확인하여 중복 생성을 방지합니다. 
- 푸시되지 않은 커밋이 있으면 PR 생성 전에 푸시할지 확인합니다.
- PR 본문에는 관련 Issue 번호를 가능한 한 연결합니다 (`Closes #123`, `Relates to #456`).
- 사용자에게 PR 내용을 먼저 보여주고 승인을 받은 후 생성합니다.
