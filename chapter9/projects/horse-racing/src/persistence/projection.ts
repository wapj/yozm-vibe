import type { RaceRecord } from "../domain/types";
import { SAVE_SCHEMA_VERSION, type GameSettings, type SavedState } from "./schema";

/**
 * `SavedState` 투영에 필요한 최소 필드. `GameStoreState`(`src/store/gameStore.ts`)가
 * 구조적으로 이 형태를 만족하므로(초과 필드 `phase`·`paused`·`horses`는 무시), store를
 * import하지 않고도 그대로 넘길 수 있다.
 */
export interface PersistableState {
  balance: number;
  bankruptcyCount: number;
  records: Record<string, RaceRecord>;
  settings: GameSettings;
}

/** store 상태에서 저장 대상 필드만 골라 `SavedState`로 투영한다. 상태 머신 필드(`phase`·`paused`)와 `horses`는 결과에 포함하지 않는다. */
export function toSavedState(state: PersistableState): SavedState {
  return {
    version: SAVE_SCHEMA_VERSION,
    balance: state.balance,
    bankruptcyCount: state.bankruptcyCount,
    records: state.records,
    settings: state.settings,
  };
}
