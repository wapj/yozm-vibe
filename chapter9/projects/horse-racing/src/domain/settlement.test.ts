import { describe, expect, it } from "vitest";
import { calculateSettlement } from "./settlement";

describe("calculateSettlement", () => {
  it("적중 시 지급액 = round(베팅액 × 배당률), 잔고 증감 = 지급액이다", () => {
    const result = calculateSettlement({ betAmount: 100, odds: 3.25, won: true });

    expect(result).toEqual({ won: true, payout: 325, balanceChange: 325 });
  });

  it("미적중 시 지급액 0, 잔고 증감 0이다", () => {
    const result = calculateSettlement({ betAmount: 500, odds: 2.5, won: false });

    expect(result).toEqual({ won: false, payout: 0, balanceChange: 0 });
  });

  it("반올림 경계: 소수 지급액은 반올림된다", () => {
    const result = calculateSettlement({ betAmount: 333, odds: 1.5, won: true });

    expect(result.payout).toBe(500);
    expect(result.balanceChange).toBe(500);
  });

  it("비정상 입력(베팅액이 최소 베팅액 미만)도 방어적 검증 없이 수식대로 계산한다", () => {
    const result = calculateSettlement({ betAmount: 50, odds: 3, won: true });

    expect(result).toEqual({ won: true, payout: 150, balanceChange: 150 });
  });

  it("비정상 입력(배당률이 1 미만)도 방어적 검증 없이 수식대로 계산한다", () => {
    const result = calculateSettlement({ betAmount: 200, odds: 0.5, won: true });

    expect(result).toEqual({ won: true, payout: 100, balanceChange: 100 });
  });
});
