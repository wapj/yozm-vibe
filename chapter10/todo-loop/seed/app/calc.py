"""주문 금액 계산 모듈."""

import os


def subtotal(items):
    """(이름, 단가, 수량) 목록의 상품 합계를 반환한다."""
    return sum(price * quantity for _, price, quantity in items)


def apply_coupon(total, code):
    # ① TODO ID는 tasks.toml의 작업과 연결한다.
    # TODO[CALC-001]: WELCOME10은 10% 할인 후 100원 단위로 내린다.
    return total


def shipping_fee(total):
    # TODO[CALC-002]: 할인 뒤 금액이 50,000원 이상이면 배송비를 무료로 한다.
    return 3_000


def get_exchange_rate(currency):
    # TODO[CALC-003]: EXPECTED_USD_RATE의 승인값을 USD에 적용한다.
    return None


def order_total(items, coupon=None):
    # TODO[CALC-004]: 할인된 상품 합계에 배송비를 더한다.
    return subtotal(items)
