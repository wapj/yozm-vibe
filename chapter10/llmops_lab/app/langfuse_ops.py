# app/langfuse_ops.py
import os
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


def record_support_run(
    ticket: SupportTicket,
    prompt: str,
    claude_result: ClaudeResult,
    eval_result: EvalResult,
):
    client = get_client()

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
            "model": claude_result.model,
        },
    ) as root:
        with propagate_attributes(
            user_id=ticket.customer_id,
            tags=["claude-p", "support", ticket.priority],
        ):
            # 모델 호출 단계
            with client.start_as_current_observation(
                name="claude-p-answer",
                as_type="generation",
                model=claude_result.model,
                input=prompt,
                output=claude_result.answer,
                metadata={
                    "duration_ms": claude_result.duration_ms,
                    "cost_usd": claude_result.cost_usd,
                },
            ):
                pass

            # 평가 단계
            with client.start_as_current_observation(
                name="quality-check",
                as_type="evaluator",
                input={"required_keywords": ticket.required_keywords},
                output={
                    "keyword_coverage": eval_result.keyword_coverage,
                    "format_ok": eval_result.format_ok,
                    "response_length_ok": eval_result.length_ok,
                },
            ):
                pass

            # score 네 개 (trace 단위)
            root.score_trace(
                name="keyword_coverage", value=eval_result.keyword_coverage
            )
            root.score_trace(
                name="format_ok", value=1.0 if eval_result.format_ok else 0.0
            )
            root.score_trace(
                name="response_length_ok", value=1.0 if eval_result.length_ok else 0.0
            )
            root.score_trace(name="latency_ms", value=claude_result.duration_ms)

        root.set_trace_io(
            input={
                "ticket_id": ticket.ticket_id,
                "subject": ticket.subject,
            },
            output=claude_result.answer,
        )

    client.flush()
