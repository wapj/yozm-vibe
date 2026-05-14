# app/history.py
import json
from datetime import datetime
from pathlib import Path
from .prompting import SupportTicket
from .claude_runner import ClaudeResult
from .evaluator import EvalResult

HISTORY_PATH = Path("artifacts/app_runs.jsonl")


def append_run(
    ticket: SupportTicket,
    claude_result: ClaudeResult,
    eval_result: EvalResult,
):
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "ticket_id": ticket.ticket_id,
        "product": ticket.product,
        "priority": ticket.priority,
        "subject": ticket.subject,
        "keyword_coverage": eval_result.keyword_coverage,
        "format_ok": eval_result.format_ok,
        "length_ok": eval_result.length_ok,
        "latency_ms": claude_result.duration_ms,
        "cost_usd": claude_result.cost_usd,
        "answer_preview": claude_result.answer[:200],
    }
    with HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
