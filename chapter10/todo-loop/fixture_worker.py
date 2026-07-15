import os
from pathlib import Path


def fixture_worker(task: dict, root: Path, attempt: int, config: dict) -> dict:
    """재시도와 이관 경로를 같은 방식으로 재현하는 시험용 작업자."""
    path = root / "workspace" / "app" / "calc.py"
    source = path.read_text(encoding="utf-8")

    replacements = {
        "CALC-001": (
            "    # TODO[CALC-001]: WELCOME10은 10% 할인 후 100원 단위로 내린다.\n"
            "    return total",
            "    if code != \"WELCOME10\":\n"
            "        return total\n"
            "    return (total * 9 // 10) // 100 * 100",
        ),
        "CALC-004": (
            "    # TODO[CALC-004]: 할인된 상품 합계에 배송비를 더한다.\n"
            "    return subtotal(items)",
            "    total = apply_coupon(subtotal(items), coupon)\n"
            "    return total + shipping_fee(total)",
        ),
    }

    if task["id"] == "CALC-002":
        old = (
            "    # TODO[CALC-002]: 할인 뒤 금액이 50,000원 이상이면 배송비를 무료로 한다.\n"
            "    return 3_000"
        )
        operator = ">" if attempt == 1 else ">="
        new = f"    return 0 if total {operator} 50_000 else 3_000"
    elif task["id"] == "CALC-003":
        rate = os.environ.get("EXPECTED_USD_RATE")
        if not rate:
            return {
                "status": "blocked",
                "reason": "운영팀이 승인한 USD 기준 환율이 없습니다.",
            }
        try:
            float(rate)
        except ValueError:
            return {"status": "error", "reason": "승인 환율이 숫자가 아닙니다."}
        old = (
            "    # TODO[CALC-003]: EXPECTED_USD_RATE의 승인값을 USD에 적용한다.\n"
            "    return None"
        )
        new = (
            '    return float(os.environ["EXPECTED_USD_RATE"]) '
            'if currency == "USD" else None'
        )
    else:
        old, new = replacements[task["id"]]

    if old not in source:
        return {"status": "error", "reason": "시작 코드를 찾지 못했습니다."}
    path.write_text(source.replace(old, new), encoding="utf-8")
    return {"status": "completed", "reason": "시험용 변경을 만들었습니다."}
