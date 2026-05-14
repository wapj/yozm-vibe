# app/evaluator.py
from dataclasses import dataclass


@dataclass
class EvalResult:
    keyword_coverage: float
    format_ok: bool
    length_ok: bool


REQUIRED_SECTIONS = ["요약", "답변", "다음 단계"]


def evaluate(answer: str, required_keywords: list[str]) -> EvalResult:
    # 키워드 커버리지: 필수 키워드 중 답변에 포함된 비율
    if required_keywords:
        hit = sum(1 for kw in required_keywords if kw in answer)
        coverage = hit / len(required_keywords)
    else:
        coverage = 1.0

    # 형식: 필수 섹션이 모두 있는지
    format_ok = all(section in answer for section in REQUIRED_SECTIONS)

    # 길이: 너무 짧거나 너무 길지 않은지
    length_ok = 50 <= len(answer) <= 4000

    return EvalResult(
        keyword_coverage=coverage,
        format_ok=format_ok,
        length_ok=length_ok,
    )
