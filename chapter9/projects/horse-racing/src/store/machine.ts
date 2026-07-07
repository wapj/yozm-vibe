import type { GamePhase } from "../domain/types";

export type GameEvent =
  | "START_COUNTDOWN"
  | "START_RACE"
  | "PAUSE"
  | "RESUME"
  | "FINISH"
  | "SETTLE"
  | "RESET";

export interface MachineState {
  phase: GamePhase;
  /** 탭 비활성화 자동 일시정지(PRD 6번, 자체 결정: 합의) 대응. racing 중에만 의미를 가진다. */
  paused: boolean;
}

export function createInitialMachineState(): MachineState {
  return { phase: "lobby", paused: false };
}

const PHASE_TRANSITIONS: Partial<Record<GamePhase, Partial<Record<GameEvent, GamePhase>>>> = {
  lobby: { START_COUNTDOWN: "countdown" },
  countdown: { START_RACE: "racing" },
  racing: { FINISH: "finish" },
  finish: { SETTLE: "settlement" },
  settlement: { RESET: "lobby" },
};

/**
 * 로비→카운트다운→경주→피니시→정산→로비 순서로만 전이한다.
 * 정의되지 않은 전이는 원래 상태를 그대로 반환한다(거부).
 * pause/resume은 phase 자체를 바꾸지 않고 racing 중 paused 플래그만 토글하며,
 * paused 상태에서는 pause/resume 외의 전이가 모두 거부된다.
 */
export function transition(state: MachineState, event: GameEvent): MachineState {
  if (event === "PAUSE") {
    if (state.phase !== "racing" || state.paused) return state;
    return { ...state, paused: true };
  }
  if (event === "RESUME") {
    if (state.phase !== "racing" || !state.paused) return state;
    return { ...state, paused: false };
  }
  if (state.paused) return state;

  const nextPhase = PHASE_TRANSITIONS[state.phase]?.[event];
  if (!nextPhase) return state;
  return { phase: nextPhase, paused: false };
}
