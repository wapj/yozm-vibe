# harness/src/harness/run.py
import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
PROMPTS = HARNESS_DIR / "prompts"  # ① 프롬프트는 harness 패키지 안에 고정


def parse_args() -> Path:
    """작업 디렉터리를 인자나 환경 변수에서 받아온다."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "project_dir",
        nargs="?",
        default=os.environ.get("PROJECT_DIR"),
        help="작업 디렉터리 (예: ../projects/rss-wiki)",
    )
    args = parser.parse_args()
    if not args.project_dir:
        print("작업 디렉터리를 지정해주세요.")
        print("사용법: uv run python -m harness.run <프로젝트 디렉터리>")
        sys.exit(1)
    return Path(args.project_dir).resolve()


ROOT = parse_args()  # ② 작업 디렉터리는 외부에서 결정
DOCS = ROOT / "docs"
STATE = DOCS / ".cycle_count"  # ③ 사이클 카운터 저장 위치

MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "50"))


def log(message: str) -> None:
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"[{timestamp}] {message}", flush=True)


def load_cycle_count() -> int:
    """이전 실행에서 저장된 사이클 번호를 읽어온다."""
    if not STATE.exists():
        return 0
    try:
        return int(STATE.read_text(encoding="utf-8").strip())
    except ValueError:
        return 0


def save_cycle_count(count: int) -> None:
    STATE.write_text(str(count), encoding="utf-8")


def bootstrap_prd() -> None:
    """PRD.md가 없으면 사용자와 대화하여 작성한다."""
    if (DOCS / "PRD.md").exists():  # ④ PRD가 이미 있으면 부트스트랩 건너뛰기
        return

    log("PRD.md가 없습니다. Planner를 대화형으로 실행합니다.")
    log("사용자와 대화하여 PRD.md를 작성한 뒤 종료하세요. (claude 종료: /exit)")

    prompt_text = (PROMPTS / "planner_bootstrap.md").read_text(encoding="utf-8")
    cmd = [
        "claude",
        "--allowedTools",
        "Read",
        "Write",
        "Edit",
        "Glob",
        "Grep",
        "--append-system-prompt",
        prompt_text,  # ⑤ 부트스트랩만 대화형 + 시스템 프롬프트로 역할 주입
    ]
    subprocess.run(cmd, cwd=ROOT)

    if not (
        DOCS / "PRD.md"
    ).exists():  # ⑥ PRD가 작성되지 않았으면 사이클 시작 전에 멈추기
        log("PRD.md가 작성되지 않았습니다. 종료합니다.")
        sys.exit(1)


def clear_done_at_cycle_start() -> None:
    """사이클 시작마다 docs/DONE을 제거해 Planner가 PRD vs 코드 간극을 재평가하게 한다.

    DONE은 영속 상태가 아니라 Planner의 사이클별 출력 신호다. PRD가 갱신되어
    새 섹션이 추가됐는데 이전 사이클이 모든 TASKS를 끝냈다는 이유만으로 종료되면,
    PRD 신규 요구가 영영 반영되지 않는다. 매 사이클 시작 시 DONE을 비우고
    Planner가 다시 판단하도록 한다(진짜로 끝났으면 Planner가 DONE을 재생성).
    """
    done = DOCS / "DONE"
    if done.exists():
        done.unlink()
        log(
            "이전 사이클의 docs/DONE을 제거했습니다. Planner가 PRD vs 코드 간극을 재평가합니다."
        )


def run_agent(
    name: str,
    prompt_file: str,
    allowed_tools: list[str],
    accept_edits: bool = False,
    model: str | None = None,
) -> int:
    prompt_path = PROMPTS / prompt_file
    prompt_text = prompt_path.read_text(encoding="utf-8")

    cmd = [
        "claude",
        "-p",
        prompt_text,
        "--allowedTools",
        *allowed_tools,
    ]  # ⑦ 사이클용 비대화형 호출
    if accept_edits:
        cmd += ["--permission-mode", "acceptEdits"]
    if model:
        cmd += ["--model", model]  # ⑧ 에이전트별 모델 지정

    log(f"--- {name} 시작 (model={model or 'default'}) ---")
    result = subprocess.run(cmd, cwd=ROOT)
    log(f"--- {name} 종료 (exit={result.returncode}) ---")
    return result.returncode


def main() -> int:
    DOCS.mkdir(exist_ok=True)
    log(f"작업 디렉터리: {ROOT}")  # ⑨ 어느 디렉터리에서 일하는지 명시
    bootstrap_prd()  # ⑩ 사이클 시작 전 PRD 부트스트랩

    start = load_cycle_count()  # ⑪ 이전 실행 이어받기
    if start > 0:
        log(f"이전 실행에서 {start} 사이클까지 진행되었습니다. 이어서 시작합니다.")

    for i in range(MAX_ITERATIONS):
        iteration = start + i + 1  # ⑫ 누적 사이클 번호
        log(f"=== 사이클 {iteration} 시작 ===")

        clear_done_at_cycle_start()  # ⑫-1 PRD 갱신을 반영하기 위해 매 사이클 DONE 초기화

        # 1. Planner — 추론이 많은 역할이므로 기본 모델(opus) 사용
        run_agent(
            "planner",
            "planner.md",
            allowed_tools=["Read", "Write", "Edit", "Glob", "Grep"],
        )  # ⑬ Planner: Bash 제외

        if (DOCS / "DONE").exists():  # ⑭ Planner 직후 종료 신호 확인
            log("PLAN의 모든 항목이 완료되었습니다. 종료.")
            save_cycle_count(iteration)  # ⑮ 종료 직전 카운터 저장
            return 0
        if (DOCS / "HALT").exists():
            log("사람의 개입이 필요합니다. docs/HALT를 확인하세요.")
            save_cycle_count(iteration)
            return 1

        # 2. Generator — sonnet 사용
        run_agent(
            "generator",
            "generator.md",
            allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
            accept_edits=True,
            model="sonnet",
        )  # ⑯ Generator: 편집 자동 승인 + sonnet

        # 3. Evaluator — sonnet 사용
        run_agent(
            "evaluator",
            "evaluator.md",
            allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
            model="sonnet",
        )  # ⑰ Evaluator: sonnet

        save_cycle_count(iteration)  # ⑱ 매 사이클 끝마다 카운터 저장
        log(f"=== 사이클 {iteration} 종료 ===")
        time.sleep(3)

    log("최대 반복 횟수에 도달했습니다. 종료.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
