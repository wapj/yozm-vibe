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
DECISIONS = DOCS / "decisions"  # 결정 합의 기록 위치

MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "50"))
PLANNER_MODEL = os.environ.get("PLANNER_MODEL", "opus")  # 계획 모델은 교체 가능
EVALUATOR_MODEL = os.environ.get("EVALUATOR_MODEL", "opus")  # 평가 모델은 교체 가능
MAX_DECISION_TRIES = 3  # 결정 합의 재시도 상한


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
        "--allowedTools", "Read", "Glob", "Grep",
        "Edit(docs/**)", "Write(docs/**)",
        "--append-system-prompt", prompt_text,  # ⑤ 부트스트랩만 대화형 + 시스템 프롬프트로 역할 주입
    ]
    subprocess.run(cmd, cwd=ROOT)

    if not (DOCS / "PRD.md").exists():  # ⑥ PRD가 작성되지 않았으면 사이클 시작 전에 멈추기
        log("PRD.md가 작성되지 않았습니다. 종료합니다.")
        sys.exit(1)


def clear_done_at_cycle_start() -> None:  # ⑦ 매 사이클 시작마다 DONE 초기화
    """사이클 시작마다 docs/DONE을 제거해 Planner가 PRD와 코드의 간극을 재평가하게 한다."""
    done = DOCS / "DONE"
    if done.exists():
        done.unlink()
        log("이전 사이클의 docs/DONE을 제거했습니다. Planner가 PRD와 코드의 간극을 재평가합니다.")


def run_agent(name: str, prompt_file: str, allowed_tools: list[str],
              accept_edits: bool = False, model: str | None = None) -> int:
    prompt_path = PROMPTS / prompt_file
    prompt_text = prompt_path.read_text(encoding="utf-8")

    cmd = ["claude", "-p", prompt_text, "--allowedTools", *allowed_tools]  # ⑧ 사이클용 비대화형 호출
    if accept_edits:
        cmd += ["--permission-mode", "acceptEdits"]
    if model:
        cmd += ["--model", model]  # ⑨ 에이전트별 모델 지정

    log(f"--- {name} 시작 (model={model or 'default'}) ---")
    result = subprocess.run(cmd, cwd=ROOT)
    log(f"--- {name} 종료 (exit={result.returncode}) ---")
    return result.returncode


def read_choice(path: Path) -> str | None:
    """선택 파일의 첫 줄에서 "선택: {라벨}"을 읽어온다."""
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    if not lines or not lines[0].startswith("선택:"):
        return None  # 형식이 어긋난 기록은 미기록으로 취급
    return lines[0].split(":", 1)[1].strip()


def resolve_decisions() -> None:  # ㉑ 결정 합의의 상태 기계
    """블라인드로 기록된 두 선택을 비교해 합의, 재시도, HALT를 판정한다."""
    if not DECISIONS.exists():
        return
    for topic in sorted(DECISIONS.glob("*.md")):
        if topic.name.endswith((".planner.md", ".evaluator.md")):
            continue
        stem = topic.name[:-3]
        p_file = DECISIONS / f"{stem}.planner.md"
        e_file = DECISIONS / f"{stem}.evaluator.md"
        p_choice, e_choice = read_choice(p_file), read_choice(e_file)
        if p_choice is None or e_choice is None:
            continue  # 아직 한쪽이 기록하지 않음
        text = topic.read_text(encoding="utf-8")
        tries = text.count("합의 불발") + 1
        if p_choice == e_choice:
            topic.write_text(text + f"\n합의: {p_choice} (시도 {tries}회)\n",
                             encoding="utf-8")
            log(f"결정 합의: {stem} → {p_choice}")
        elif tries >= MAX_DECISION_TRIES:
            halt = (f"결정 합의 {MAX_DECISION_TRIES}회 불발: {stem}\n\n"
                    f"[planner]\n{p_file.read_text(encoding='utf-8')}\n\n"
                    f"[evaluator]\n{e_file.read_text(encoding='utf-8')}\n")
            (DOCS / "HALT").write_text(halt, encoding="utf-8")
            log(f"결정 합의 불발로 HALT: {stem}")
        else:
            topic.write_text(text + "\n합의 불발. 후보를 처음부터 다시 나열하고 "
                                    "장단점을 비교한 뒤 결정하라.\n",
                             encoding="utf-8")
            log(f"결정 합의 불발({tries}회): {stem} — 재시도")
        p_file.unlink()
        e_file.unlink()  # 선택 파일을 지워 다음 시도도 블라인드로 시작


def main() -> int:
    DOCS.mkdir(exist_ok=True)
    log(f"작업 디렉터리: {ROOT}")  # ⑩ 어느 디렉터리에서 일하는지 명시
    bootstrap_prd()  # ⑪ 사이클 시작 전 PRD 부트스트랩

    start = load_cycle_count()  # ⑫ 이전 실행 이어받기
    if start > 0:
        log(f"이전 실행에서 {start} 사이클까지 진행되었습니다. 이어서 시작합니다.")

    for i in range(MAX_ITERATIONS):
        iteration = start + i + 1  # ⑬ 누적 사이클 번호
        log(f"=== 사이클 {iteration} 시작 ===")

        clear_done_at_cycle_start()  # ⑭ PRD 갱신을 반영하기 위해 매 사이클 DONE 초기화

        # 1. Planner — 추론이 많은 역할이라 기본 opus, PLANNER_MODEL로 교체 가능
        run_agent("planner", "planner.md",
                  allowed_tools=["Read", "Glob", "Grep",
                                 "Edit(docs/**)", "Write(docs/**)"],
                  model=PLANNER_MODEL)  # ⑮ Planner: Bash 제외, 편집은 docs/만

        if (DOCS / "DONE").exists():  # ⑯ Planner 직후 종료 신호 확인
            log("PLAN의 모든 항목이 완료되었습니다. 종료.")
            save_cycle_count(iteration)  # ⑰ 종료 직전 카운터 저장
            return 0
        if (DOCS / "HALT").exists():
            log("사람의 개입이 필요합니다. docs/HALT를 확인하세요.")
            save_cycle_count(iteration)
            return 1

        # 2. Generator — sonnet 사용
        run_agent("generator", "generator.md",
                  allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
                  accept_edits=True,
                  model="sonnet")  # ⑱ Generator: 편집 자동 승인 + sonnet

        # 3. Evaluator — 기본 opus, EVALUATOR_MODEL로 교체 가능
        run_agent("evaluator", "evaluator.md",
                  allowed_tools=["Read", "Glob", "Grep", "Bash",
                                 "Edit(docs/**)", "Write(docs/**)"],
                  model=EVALUATOR_MODEL)  # ⑲ Evaluator: 편집은 docs/만

        resolve_decisions()  # ㉒ 두 기록이 모두 모인 사이클 말미에 합의 판정
        if (DOCS / "HALT").exists():
            log("사람의 개입이 필요합니다. docs/HALT를 확인하세요.")
            save_cycle_count(iteration)
            return 1

        save_cycle_count(iteration)  # ⑳ 매 사이클 끝마다 카운터 저장
        log(f"=== 사이클 {iteration} 종료 ===")
        time.sleep(3)

    log("최대 반복 횟수에 도달했습니다. 종료.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
