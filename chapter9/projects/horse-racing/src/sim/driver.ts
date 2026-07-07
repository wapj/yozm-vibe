/**
 * 렌더 루프가 소비할 고정 스텝 accumulator와 전체 경주 완주 구동기(PRD 4.5, 5번).
 * raf 기반 실시간 루프·DOM 이벤트 연결은 T10의 몫이며, 여기서는 시간을 인자로
 * 받는 순수 함수만 다룬다.
 */
import { rankRunners, step, createRaceState } from "./engine";
import type { RaceParticipant, RaceState, RankedRunner } from "./types";

/** accumulator가 한 번에 소비하는 서브스텝 길이(초). 60fps 프레임 하나에 해당한다. */
export const FIXED_SUBSTEP = 1 / 60;

/** 프레임마다 남은 dt를 들고 다니는 누적 버퍼. */
export interface FixedStepAccumulator {
  buffer: number;
}

export function createAccumulator(): FixedStepAccumulator {
  return { buffer: 0 };
}

/**
 * 원시 dt(가변, 예: raf가 넘기는 실제 프레임 시간)를 accumulator에 누적하고,
 * fixedStep 단위로 나눠떨어지는 만큼만 정확히 그 개수의 스텝을 진행한다.
 * 나머지(fixedStep 미만)는 다음 호출을 위해 accumulator에 남겨 다음 프레임과
 * 합산되므로, 프레임레이트가 들쭉날쭉해도 시뮬레이션은 항상 동일한 fixedStep
 * 단위로만 전진해 결과가 프레임레이트와 무관해진다.
 */
export function advanceWithAccumulator(
  state: RaceState,
  accumulator: FixedStepAccumulator,
  rawDt: number,
  rng: () => number,
  fixedStep: number = FIXED_SUBSTEP,
): { state: RaceState; accumulator: FixedStepAccumulator } {
  let buffer = accumulator.buffer + Math.max(0, rawDt);
  let current = state;

  while (buffer >= fixedStep && !current.finished) {
    current = step(current, fixedStep, rng);
    buffer -= fixedStep;
  }

  return {
    state: current,
    accumulator: { buffer: current.finished ? 0 : buffer },
  };
}

export interface RaceRunResult {
  finalState: RaceState;
  /** 완주 시각(초). 아무도 완주하지 못하고 maxTime에 도달했다면 maxTime과 같다. */
  finishTime: number;
  rankings: RankedRunner[];
}

/**
 * 출전마 목록으로 경주를 초기화해 완주(또는 안전 상한 maxTime)까지 고정 스텝으로
 * 진행한 뒤 최종 상태를 반환하는 순수 구동 함수. fixedStep은 accumulator와 같은
 * 기본값을 쓰되, 실측·테스트를 위해 더 잘게 쪼갤 수 있도록 인자로 받는다.
 */
export function runRaceToCompletion(
  participants: RaceParticipant[],
  rng: () => number = Math.random,
  options?: { fixedStep?: number; maxTime?: number },
): RaceRunResult {
  const fixedStep = options?.fixedStep ?? FIXED_SUBSTEP;
  const maxTime = options?.maxTime ?? 120;

  let state = createRaceState(participants, rng);
  while (!state.finished && state.elapsedTime < maxTime) {
    state = step(state, fixedStep, rng);
  }

  return {
    finalState: state,
    finishTime: state.elapsedTime,
    rankings: rankRunners(state.runners),
  };
}
