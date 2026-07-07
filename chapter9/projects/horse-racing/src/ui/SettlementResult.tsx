export interface SettlementResultProps {
  won: boolean;
  payout: number;
  balanceAfter: number;
}

/**
 * PRD 4.3·5번: 정산 계산 결과(적중/미적중·지급액·정산 후 잔고)를 표시한다.
 * 색상만으로 결과를 구분하지 않도록 "적중"/"미적중" 텍스트를 병기한다.
 * 실제 경주 결과에서 이 props를 조립하고 adjustBalance로 잔고에 반영하는
 * 배선은 T20의 몫이며, 이 컴포넌트는 계산된 결과만 소비한다.
 */
export function SettlementResult({ won, payout, balanceAfter }: SettlementResultProps) {
  const outcomeClass = won ? "settlement-result--won" : "settlement-result--lost";

  return (
    <section className={`card settlement-result ${outcomeClass}`} aria-label="정산 결과">
      <p>{won ? "적중" : "미적중"}</p>
      <p>{`지급액: ${payout.toLocaleString("ko-KR")}`}</p>
      <p>{`정산 후 잔고: ${balanceAfter.toLocaleString("ko-KR")}`}</p>
    </section>
  );
}
