import { createHorseCatalog } from "../domain/horses";
import { updateRecordsWithRaceResult } from "../domain/records";
import type { HorseProfile, RaceRecord } from "../domain/types";
import { DEFAULT_BALANCE, type GameSettings, type SavedState } from "../persistence/schema";
import type { RankedRunner } from "../sim/types";
import { createInitialMachineState, transition, type GameEvent, type MachineState } from "./machine";

/** PRD 4.3: 베팅 최소 금액이자 파산 판정 기준(잔고가 이 값 미만이면 파산). */
export const MIN_BET_AMOUNT = 100;

export interface GameStoreState extends MachineState {
  balance: number;
  bankruptcyCount: number;
  records: Record<string, RaceRecord>;
  settings: GameSettings;
  horses: HorseProfile[];
}

export interface GameStore {
  getState(): GameStoreState;
  subscribe(listener: (state: GameStoreState) => void): () => void;
  dispatch(event: GameEvent): void;
  /** 잔고를 delta만큼 증감시키고, 파산(잔고 < MIN_BET_AMOUNT) 여부를 판정해 필요하면 재충전한다. */
  adjustBalance(delta: number): void;
  /** 완주 순위로 출전마들의 전적(`records`)을 갱신하고 구독자에게 emit한다. */
  recordRaceResult(rankings: RankedRunner[]): void;
}

/** 구독 기반 커스텀 스토어. 상태 머신(phase/paused)과 저장 계층 데이터(잔고·전적·설정)를 함께 관리한다. */
export function createGameStore(saved: SavedState): GameStore {
  let machineState: MachineState = createInitialMachineState();
  let balance = saved.balance;
  let bankruptcyCount = saved.bankruptcyCount;
  let records = { ...saved.records };
  const settings = { ...saved.settings };
  const horses = createHorseCatalog(settings.horseCount);

  const listeners = new Set<(state: GameStoreState) => void>();

  function getState(): GameStoreState {
    return { ...machineState, balance, bankruptcyCount, records, settings, horses };
  }

  function emit(): void {
    const state = getState();
    for (const listener of listeners) listener(state);
  }

  function applyBankruptcyCheck(): void {
    if (balance < MIN_BET_AMOUNT) {
      balance = DEFAULT_BALANCE;
      bankruptcyCount += 1;
    }
  }

  return {
    getState,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    dispatch(event) {
      machineState = transition(machineState, event);
      emit();
    },
    adjustBalance(delta) {
      balance += delta;
      applyBankruptcyCheck();
      emit();
    },
    recordRaceResult(rankings) {
      records = updateRecordsWithRaceResult(records, rankings);
      emit();
    },
  };
}
