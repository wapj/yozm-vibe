/** T20b: 오케스트레이션 훅(useGameController)이 주입받는 타이머 인터페이스. */
export interface TimerSource {
  schedule(callback: () => void, delayMs: number): number;
  cancel(handle: number): void;
}
