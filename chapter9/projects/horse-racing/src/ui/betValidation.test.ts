import { describe, expect, it } from "vitest";
import { validateBetAmount } from "./betValidation";

describe("validateBetAmount", () => {
  it("최소 금액(100) 미만이면 무효", () => {
    expect(validateBetAmount(99, 10000)).toEqual({ valid: false, reason: "최소 금액 미만" });
  });

  it("잔고를 초과하면 무효", () => {
    expect(validateBetAmount(200, 100)).toEqual({ valid: false, reason: "잔고 초과" });
  });

  it("정수가 아니면 무효", () => {
    expect(validateBetAmount(100.5, 10000)).toEqual({ valid: false, reason: "정수 아님" });
  });

  it("100 이상·잔고 이하의 정수면 유효", () => {
    expect(validateBetAmount(500, 10000)).toEqual({ valid: true });
  });

  it("경계값: 정확히 100이면 유효", () => {
    expect(validateBetAmount(100, 10000)).toEqual({ valid: true });
  });

  it("경계값: 정확히 잔고와 같으면 유효", () => {
    expect(validateBetAmount(10000, 10000)).toEqual({ valid: true });
  });
});
