---
name: create-pr
description: 현재 브랜치의 커밋과 변경 사항을 분석해 GitHub Pull Request 제목과 본문을 작성하고, 승인 후 gh CLI로 PR을 생성합니다. "PR 만들어줘", "풀리퀘스트 생성", "PR 올려줘" 요청에 사용합니다.
allowed-tools: Bash(git branch *) Bash(git log *) Bash(git diff *) Bash(gh pr view *) Bash(gh pr status *)
---

# GitHub PR Creator Skill

## Current branch

!`git branch --show-current`

## Commits against main

!`git log main..HEAD --oneline`

## Diff stat

!`git diff main..HEAD --stat`

## Goal

현재 브랜치의 변경 사항을 분석하여 구조화된 Pull Request를 생성합니다.

## Instructions

1. 현재 브랜치가 `main`이면 새 작업 브랜치 생성을 제안합니다.
2. 푸시되지 않은 커밋이 있으면 PR 생성 전에 push 필요 여부를 확인합니다.
3. `resources/pr_template.md`를 읽고 PR 본문을 채웁니다.
4. 관련 Issue 번호가 있으면 `Closes #123` 또는 `Relates to #123`로 연결합니다.
5. PR 제목과 본문을 사용자에게 보여주고 승인받습니다.
6. 승인 후 `gh pr create --title "<제목>" --body "<본문>" --base main`을 실행합니다.

## Constraints

- PR 생성 전 저장소, base 브랜치, 현재 브랜치를 명확히 보여줍니다.
- UI 변경이 있으면 PR 본문에 스크린샷 필요 항목을 남깁니다.
- 사용자의 승인 없이 push나 PR 생성 명령을 실행하지 않습니다.
