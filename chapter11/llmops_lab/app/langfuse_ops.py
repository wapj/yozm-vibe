# app/langfuse_ops.py
import os
from contextlib import contextmanager

from langfuse import Langfuse, propagate_attributes

from .prompting import SupportTicket
from .claude_runner import ClaudeResult
from .evaluator import EvalResult


_client = None


def get_client() -> Langfuse:
    global _client
    if _client is None:
        _client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_BASE_URL"),
        )
    return _client


@contextmanager
def support_ticket_trace(ticket: SupportTicket):
    """티켓 한 건의 root span을 열고 trace 속성을 전파한다."""
    client = get_client()
    try:
        with client.start_as_current_observation(
            name="support-ticket-run",
            as_type="span",
            input={
                "ticket_id": ticket.ticket_id,
                "subject": ticket.subject,
                "message": ticket.message,
            },
            metadata={
                "product": ticket.product,
                "priority": ticket.priority,
            },
        ) as root:
            with propagate_attributes(
                user_id=ticket.customer_id,
                tags=["claude-p", "support", ticket.priority],
            ):
                yield root
    finally:
        client.flush()


@contextmanager
def claude_generation(prompt_text: str, model: str, prompt=None):
    """Claude 호출을 감싸는 generation span."""
    client = get_client()
    kwargs = {
        "name": "claude-p-answer",
        "as_type": "generation",
        "model": model,
        "input": prompt_text,
    }
    if prompt is not None:
        kwargs["prompt"] = prompt

    with client.start_as_current_observation(**kwargs) as gen:
        yield gen


@contextmanager
def quality_evaluator(required_keywords: list[str]):
    """평가 단계를 감싸는 evaluator span."""
    client = get_client()
    with client.start_as_current_observation(
        name="quality-check",
        as_type="evaluator",
        input={"required_keywords": required_keywords},
    ) as ev:
        yield ev


def record_scores(
    root,
    claude_result: ClaudeResult,
    eval_result: EvalResult,
):
    """trace 단위 score 4종을 기록한다."""
    root.score_trace(name="keyword_coverage", value=eval_result.keyword_coverage)
    root.score_trace(name="format_ok", value=1.0 if eval_result.format_ok else 0.0)
    root.score_trace(
        name="response_length_ok", value=1.0 if eval_result.length_ok else 0.0
    )
    root.score_trace(name="latency_ms", value=claude_result.duration_ms)
