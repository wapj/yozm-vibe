import os

from workspace.app.calc import (
    apply_coupon,
    get_exchange_rate,
    order_total,
    shipping_fee,
)


def test_calc_001_coupon():  # ① 설명이 아닌 실행 결과로 완료 판정
    assert apply_coupon(12_345, "WELCOME10") == 11_100
    assert apply_coupon(12_345, "UNKNOWN") == 12_345
    assert apply_coupon(99, "WELCOME10") == 0
    assert apply_coupon(1_000_000_000_000_000_065, "WELCOME10") == 900_000_000_000_000_000


def test_calc_002_shipping():
    assert shipping_fee(49_999) == 3_000
    assert shipping_fee(50_000) == 0  # ② 경계값 포함
    assert shipping_fee(80_000) == 0


def test_calc_003_exchange_rate():  # ③ 외부 승인값 확인
    expected = os.environ.get("EXPECTED_USD_RATE")
    assert expected, "운영팀이 승인한 EXPECTED_USD_RATE가 필요합니다."
    assert get_exchange_rate("USD") == float(expected)
    assert get_exchange_rate("EUR") is None


def test_calc_004_order_total():  # ④ 앞서 구현한 기능의 조합 확인
    assert order_total([("원두", 40_000, 1)], "WELCOME10") == 39_000
    assert order_total([("원두", 60_000, 1)], "WELCOME10") == 54_000
    assert order_total([("원두", 50_000, 1)]) == 50_000
