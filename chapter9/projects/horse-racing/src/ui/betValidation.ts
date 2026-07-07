import { MIN_BET_AMOUNT } from "../store/gameStore";

export type BetInvalidReason = "최소 금액 미만" | "잔고 초과" | "정수 아님";

export interface BetValidationResult {
  valid: boolean;
  reason?: BetInvalidReason;
}

/** PRD 4.3: 베팅 금액이 최소 베팅액 이상·잔고 이하의 정수인지 검증한다. */
export function validateBetAmount(amount: number, balance: number): BetValidationResult {
  if (!Number.isInteger(amount)) {
    return { valid: false, reason: "정수 아님" };
  }
  if (amount < MIN_BET_AMOUNT) {
    return { valid: false, reason: "최소 금액 미만" };
  }
  if (amount > balance) {
    return { valid: false, reason: "잔고 초과" };
  }
  return { valid: true };
}
