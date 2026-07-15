import argparse
import json
import os
import shutil
import subprocess
import sys
import tomllib
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from workers import run_worker


ROOT = Path(__file__).parent.resolve()
WORKSPACE = ROOT / "workspace"
TARGET = WORKSPACE / "app" / "calc.py"
RUNTIME = ROOT / ".loop"
STATE = RUNTIME / "state.json"
EVENTS = RUNTIME / "events.jsonl"
BACKUP = RUNTIME / "before.py"
EVIDENCE = RUNTIME / "evidence"
HANDOFF = RUNTIME / "handoff"
RUNNABLE = {"pending", "retry"}


def load_toml(name: str, key: str):
    with (ROOT / name).open("rb") as file:
        return tomllib.load(file)[key]  # ① 계약과 예산은 코드 밖에서 읽기


def load_state() -> dict:
    if not STATE.exists():
        raise FileNotFoundError("먼저 reset을 실행하세요.")
    return json.loads(STATE.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    RUNTIME.mkdir(exist_ok=True)
    temporary = STATE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, STATE)  # ② 반쯤 기록된 상태 파일 방지


def record(event: str, task_id: str | None = None, **details) -> None:
    row = {"time": datetime.now(UTC).isoformat(), "event": event, **details}
    if task_id:
        row["task_id"] = task_id
    with EVENTS.open("a", encoding="utf-8") as file:
        file.write(json.dumps(row, ensure_ascii=False) + "\n")  # ③ 상태 변화 누적


def reset(tasks: list[dict]) -> None:  # ④ 시작 코드 확인과 첫 상태 생성
    if WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)
    if RUNTIME.exists():
        shutil.rmtree(RUNTIME)
    shutil.copytree(ROOT / "seed", WORKSPACE)

    source = TARGET.read_text(encoding="utf-8")
    missing = [task["id"] for task in tasks if task["marker"] not in source]
    if missing:
        raise ValueError("시작 코드에서 TODO를 찾지 못했습니다: " + ", ".join(missing))
    state = {
        "tasks": {
            task["id"]: {"status": "pending", "attempts": 0, "reason": ""}
            for task in tasks
        },
        "calls": 0,
        "active": None,
    }
    save_state(state)
    record("reset", discovered=len(tasks))
    print(f"[reset] TODO {len(tasks)}건을 발견했습니다.")


def task_map(tasks: list[dict]) -> dict[str, dict]:
    return {task["id"]: task for task in tasks}


def write_handoff(task: dict, item: dict) -> Path:
    HANDOFF.mkdir(exist_ok=True)
    path = HANDOFF / f"{task['id']}.md"
    path.write_text(
        f"# {task['id']}: {task['title']}\n\n"
        f"- 상태: {item['status']}\n"
        f"- 시도: {item['attempts']}/{task['max_attempts']}\n"
        f"- 이유: {item['reason']}\n\n"
        f"## 완료 조건\n\n{task['description']}\n",
        encoding="utf-8",
    )  # ⑤ 사람이 이어받을 정보 남기기
    return path


def recover(state: dict, tasks: list[dict]) -> None:
    task_id = state.get("active")
    if not task_id:
        return
    item = state["tasks"][task_id]
    task = task_map(tasks)[task_id]
    restored = BACKUP.exists()
    if not restored:
        item["status"] = "needs_human"
        item["reason"] = "중단된 변경을 되돌릴 기준본이 없습니다."
        write_handoff(task, item)
    else:
        shutil.copy2(BACKUP, TARGET)
        item["status"] = (
            "retry" if item["attempts"] < task["max_attempts"] else "needs_human"
        )
        item["reason"] = "이전 실행이 중단되어 변경을 되돌렸습니다."
        if item["status"] == "needs_human":
            write_handoff(task, item)
    state["active"] = None
    BACKUP.unlink(missing_ok=True)
    save_state(state)  # ⑥ 다음 실행이 중단된 작업을 복구
    record("recovered", task_id)
    if restored:
        print(f"[recover] {task_id}의 검증 전 변경을 되돌렸습니다.")
    else:
        print(f"[handoff] {task_id}의 복구 기준본이 없어 사람에게 넘겼습니다.")


def next_task(tasks: list[dict], state: dict) -> dict | None:
    for task in tasks:
        item = state["tasks"][task["id"]]
        if item["status"] not in RUNNABLE:
            continue
        if all(
            state["tasks"][dependency]["status"] == "passed"
            for dependency in task.get("depends_on", [])
        ):
            return task  # ⑦ 선행 작업이 끝난 첫 작업 배정
    return None


def verify(task: dict, state: dict, tasks: list[dict], config: dict) -> tuple[bool, str]:
    if task["marker"] in TARGET.read_text(encoding="utf-8"):
        passed, output = False, f"{task['marker']} 주석이 남아 있습니다."
    else:
        by_id = task_map(tasks)
        checks = [
            by_id[task_id]["check"]
            for task_id, item in state["tasks"].items()
            if item["status"] == "passed"
        ]
        checks.append(task["check"])  # ⑧ 현재 작업과 이전 완료 작업을 함께 검사
        try:
            process = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", *dict.fromkeys(checks)],
                cwd=ROOT,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=float(config["verify_timeout_seconds"]),
            )
            output = (process.stdout + process.stderr).strip()
            passed = process.returncode == 0
        except subprocess.TimeoutExpired:
            passed, output = False, "검증 시간이 상한을 넘었습니다."

    EVIDENCE.mkdir(exist_ok=True)
    attempt = state["tasks"][task["id"]]["attempts"]
    (EVIDENCE / f"{task['id']}-{attempt}.txt").write_text(
        output + "\n", encoding="utf-8"
    )  # ⑨ 완료 판정의 근거 보관
    return passed, output


def restore() -> None:
    shutil.copy2(BACKUP, TARGET)
    BACKUP.unlink(missing_ok=True)


def run_one(task: dict, state: dict, tasks: list[dict], config: dict, worker: str) -> str:
    item = state["tasks"][task["id"]]
    previous_status = item["status"]
    item["attempts"] += 1
    attempt = item["attempts"]
    shutil.copy2(TARGET, BACKUP)  # ⑩ 작업 전에 되돌릴 기준본 저장
    item["status"] = "running"
    state["active"] = task["id"]
    state["calls"] += 1
    save_state(state)
    record("claimed", task["id"], attempt=attempt, worker=worker)
    kind = "실제 LLM 호출" if worker == "claude" else "LLM 호출 없음"
    print(
        f"[claim] {task['id']} worker={worker} ({kind}) "
        f"attempt={attempt}/{task['max_attempts']}",
        flush=True,
    )

    worker_task = {**task, "feedback": item["reason"]}
    result = run_worker(worker, worker_task, ROOT, attempt, config)
    if result["status"] == "blocked":
        restore()
        item.update(status="needs_human", reason=result["reason"])
        outcome = "needs_human"  # ⑪ 외부 결정이 필요한 작업은 재시도하지 않기
    elif result["status"] == "error":
        restore()
        item["attempts"] -= 1
        item["status"] = previous_status
        item["reason"] = result["reason"]
        outcome = "infrastructure_error"
    else:
        item["status"] = "verifying"
        save_state(state)
        passed, evidence = verify(task, state, tasks, config)
        if passed:
            BACKUP.unlink(missing_ok=True)
            item.update(status="passed", reason="")
            outcome = "passed"
        else:
            restore()  # ⑫ 검증에 실패한 변경 복원
            item["status"] = (
                "retry" if attempt < task["max_attempts"] else "needs_human"
            )  # ⑬ 시도 상한 안에서만 재시도
            item["reason"] = evidence
            outcome = item["status"]

    state["active"] = None
    save_state(state)
    record(outcome, task["id"], reason=item["reason"])
    if outcome == "infrastructure_error":
        print(f"[halt] 작업자 실행 오류: {item['reason']}")
    elif outcome == "needs_human":
        report = write_handoff(task, item)
        print(f"[handoff] {task['id']} -> needs_human ({report.relative_to(ROOT)})")
    else:
        print(f"[verify] {task['id']} -> {outcome}")
    return outcome


def finish(state: dict, tasks: list[dict]) -> int:
    counts = Counter(item["status"] for item in state["tasks"].values())
    if counts["passed"] == len(tasks):
        print(f"[done] {len(tasks)}/{len(tasks)}건 완료")
        return 0
    waiting = counts["pending"] + counts["retry"]
    print(
        f"[partial] 완료 {counts['passed']}, "
        f"사람 확인 {counts['needs_human']}, 대기 {waiting}"
    )
    return 2  # ⑭ 자동 처리는 끝났지만 사람 확인이 남은 상태


def run_loop(tasks: list[dict], config: dict, worker: str, once: bool) -> int:
    state = load_state()
    recover(state, tasks)
    while True:
        task = next_task(tasks, state)
        if task is None:
            return finish(state, tasks)
        if state["calls"] >= int(config["max_calls"]):  # ⑮ 전체 작업자 호출 상한
            print(f"[budget] 작업자 호출 상한 {config['max_calls']}회에 도달했습니다.")
            return 3
        outcome = run_one(task, state, tasks, config, worker)
        if outcome == "infrastructure_error":
            return 4
        if once:
            return 0 if outcome == "passed" else 2


def status(tasks: list[dict]) -> None:
    state = load_state()  # ⑯ 저장된 진행 상태 이어받기
    recover(state, tasks)
    print("ID        상태          시도  작업")
    for task in tasks:
        item = state["tasks"][task["id"]]
        print(
            f"{task['id']:<9} {item['status']:<13} "
            f"{item['attempts']}/{task['max_attempts']}   {task['title']}"
        )
    print(f"작업자 호출 {state['calls']}회")


def requeue(task_id: str, reason: str, tasks: list[dict]) -> None:
    state = load_state()
    if task_id not in task_map(tasks):
        raise ValueError(f"알 수 없는 작업 ID: {task_id}")
    item = state["tasks"][task_id]
    if item["status"] != "needs_human":
        raise ValueError("사람에게 이관한 작업만 다시 등록할 수 있습니다.")
    item.update(status="pending", attempts=0, reason=reason)  # ⑰ 사람의 판단 반영
    save_state(state)
    (HANDOFF / f"{task_id}.md").unlink(missing_ok=True)
    record("requeued", task_id, reason=reason)
    print(f"[requeue] {task_id} -> pending")


def simulate(tasks: list[dict], config: dict, approved_rate: str, confirmed: bool) -> int:
    """책의 재시도, 사람 이관, 재등록 흐름을 한 번에 실행한다."""
    try:
        if float(approved_rate) <= 0:
            raise ValueError
    except ValueError as error:
        raise ValueError("승인 환율은 0보다 큰 숫자여야 합니다.") from error

    if not confirmed and (WORKSPACE.exists() or RUNTIME.exists()):
        answer = input("workspace와 .loop를 초기화합니다. 계속할까요? [y/N] ")
        if answer.strip().lower() not in {"y", "yes"}:
            print("[simulate] 취소했습니다.")
            return 2

    worker = "fixture"
    print("[simulate] worker=fixture: LLM 호출 없는 결정적 재현", flush=True)
    previous_rate = os.environ.pop("EXPECTED_USD_RATE", None)
    try:
        print("\n[1단계] 승인값 없이 루프를 실행합니다.")
        reset(tasks)
        first_result = run_loop(tasks, config, worker, once=False)
        status(tasks)

        current = load_state()
        report = HANDOFF / "CALC-003.md"
        if (
            first_result != 2
            or current["tasks"]["CALC-003"]["status"] != "needs_human"
            or not report.exists()
        ):
            raise ValueError("CALC-003의 사람 이관 상태를 재현하지 못했습니다.")

        print("\n[2단계] 사람이 확인할 이관 보고서입니다.\n")
        print(report.read_text(encoding="utf-8"))

        print(f"[3단계] 운영팀 승인값 {approved_rate}를 반영해 다시 실행합니다.")
        os.environ["EXPECTED_USD_RATE"] = approved_rate
        requeue(
            "CALC-003",
            f"운영팀이 USD 기준 환율 {approved_rate}를 승인함",
            tasks,
        )
        final_result = run_loop(tasks, config, worker, once=False)
        status(tasks)
        if final_result != 0:
            return final_result

        print("\n[4단계] 전체 완료 조건을 다시 검사합니다.", flush=True)
        acceptance = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "checks"],
            cwd=ROOT,
            timeout=float(config["verify_timeout_seconds"]),
        )
        return acceptance.returncode
    finally:
        if previous_rate is None:
            os.environ.pop("EXPECTED_USD_RATE", None)
        else:
            os.environ["EXPECTED_USD_RATE"] = previous_rate


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="TODO 작업을 운영하는 실습용 루프")
    sub = command.add_subparsers(dest="command", required=True)
    sub.add_parser("reset")
    sub.add_parser("status")

    run = sub.add_parser("run")
    run.add_argument("--once", action="store_true")
    run.add_argument("--worker", choices=("manual", "fixture", "claude"), default="manual")
    run.add_argument("--max-calls", type=int)

    simulation = sub.add_parser("simulate")
    simulation.add_argument("--approved-rate", default="1325.5")
    simulation.add_argument("--yes", action="store_true")

    resume = sub.add_parser("requeue")
    resume.add_argument("task_id")
    resume.add_argument("--reason", required=True)
    return command


def main() -> int:
    args = parser().parse_args()
    tasks = load_toml("tasks.toml", "tasks")
    config = load_toml("loop.toml", "loop")
    if getattr(args, "max_calls", None) is not None:
        if args.max_calls < 1:
            raise ValueError("호출 상한은 1 이상이어야 합니다.")
        config["max_calls"] = args.max_calls

    if args.command == "reset":
        reset(tasks)
        return 0
    if args.command == "status":
        status(tasks)
        return 0
    if args.command == "requeue":
        requeue(args.task_id, args.reason, tasks)
        return 0
    if args.command == "simulate":
        return simulate(tasks, config, args.approved_rate, args.yes)
    return run_loop(tasks, config, args.worker, args.once)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError) as error:
        print(f"[error] {error}", file=sys.stderr)
        raise SystemExit(4)
