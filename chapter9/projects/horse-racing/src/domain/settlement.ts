export interface SettlementInput {
  betAmount: number;
  odds: number;
  won: boolean;
}

export interface SettlementOutcome {
  won: boolean;
  payout: number;
  balanceChange: number;
}

/**
 * PRD 4.3: 베팅은 베팅 시점에 선차감되므로, 정산 시점의 잔고 증감은 적중 시
 * 지급액(베팅액 × 배당률의 반올림)만큼 증가, 미적중 시 0이다. 베팅액 최소값
 * (MIN_BET_AMOUNT)·배당률 하한(1)의 방어는 베팅 확정 이전 단계(betValidation.ts·
 * calculateOdds)에서 이미 이뤄지므로, 이 함수는 입력을 재검증하지 않고 수식
 * 그대로 계산한다(명시적 계약: 비정상 입력도 방어적 분기 없이 동일한 수식으로 처리).
 */
export function calculateSettlement({ betAmount, odds, won }: SettlementInput): SettlementOutcome {
  if (!won) {
    return { won: false, payout: 0, balanceChange: 0 };
  }
  const payout = Math.round(betAmount * odds);
  return { won: true, payout, balanceChange: payout };
}
