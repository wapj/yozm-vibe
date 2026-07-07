import type { GameStore } from "../store/gameStore";
import { useGameStore } from "./useGameStore";

export interface BalanceDisplayProps {
  store: GameStore;
}

/** PRD 4.4: 잔고·파산 횟수를 노출한다. */
export function BalanceDisplay({ store }: BalanceDisplayProps) {
  const { balance, bankruptcyCount } = useGameStore(store);

  return (
    <section className="balance-display" aria-label="잔고 정보">
      <p>잔고: {balance.toLocaleString("ko-KR")}원</p>
      <p>파산 횟수: {bankruptcyCount}회</p>
    </section>
  );
}
