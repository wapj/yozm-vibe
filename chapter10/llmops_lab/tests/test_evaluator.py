# tests/test_evaluator.py
import pytest

from app.evaluator import evaluate


GOOD_ANSWER = """
## 요약
환불은 결제일로부터 7영업일 이내 가능합니다.

## 답변
영수증을 첨부해 고객센터로 문의해 주세요.

## 다음 단계
1. 영수증 준비
2. 고객센터 연락
"""


def test_evaluate_passes_well_formed_answer():
    result = evaluate(
        answer=GOOD_ANSWER,
        required_keywords=["환불", "결제일", "영업일", "영수증"],
    )
    assert result.keyword_coverage == 1.0
    assert result.format_ok is True
    assert result.length_ok is True


def test_evaluate_detects_missing_section():
    answer = "환불은 가능합니다. 영수증을 보내주세요."  # 섹션 없음
    result = evaluate(answer, required_keywords=["환불"])
    assert result.format_ok is False


def test_evaluate_calculates_partial_coverage():
    answer = "## 요약\n## 답변\n## 다음 단계\n환불만 가능합니다."
    result = evaluate(answer, required_keywords=["환불", "결제일", "영수증"])
    assert result.keyword_coverage == pytest.approx(1 / 3)
