#!/bin/bash
# ralph.sh
set -u
mkdir -p docs

while :; do
  if [[ -f docs/TASKS.md ]] && ! grep -q '^- \[ \]' docs/TASKS.md; then
    echo "TASKS.md 에 남은 항목이 없습니다. 종료."
    break
  fi

  echo "=== $(date -Iseconds) 반복 시작 ==="
  claude -p "$(cat PROMPT.md)" \
    --permission-mode acceptEdits \
    --allowedTools Read Write Edit Bash Glob Grep
  echo "=== 반복 종료 ==="
  sleep 3
done
