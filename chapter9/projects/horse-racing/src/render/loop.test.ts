import { describe, expect, it } from "vitest";
import { createRenderLoop } from "./loop";
import { createRaceState } from "../sim/engine";
import { createSeededRng } from "../sim/rng";
import { createInitialMachineState, transition, type GameEvent } from "../store/machine";
import { TRACK_LENGTH, type RaceState } from "../sim/types";
import { SLOW_MOTION_TIME_SCALE } from "./types";
import type { RafSource, VisibilitySource } from "./types";

/** 실제 requestAnimationFrame 대신, 테스트가 프레임 타임스탬프를 직접 통제하는 가짜 raf. */
function createManualRaf(): RafSource & { tick(timeMs: number): void } {
  let pending: ((timeMs: number) => void) | null = null;
  let handleCounter = 0;
  return {
    request(callback) {
      pending = callback;
      return ++handleCounter;
    },
    cancel() {
      pending = null;
    },
    tick(timeMs: number) {
      const callback = pending;
      pending = null;
      callback?.(timeMs);
    },
  };
}

/** 실제 visibilitychange 대신, 테스트가 hidden 통지를 직접 발생시키는 가짜 visibility 소스. */
function createManualVisibility(): VisibilitySource & { emit(hidden: boolean): void } {
  let listener: ((hidden: boolean) => void) | null = null;
  return {
    subscribe(onChange) {
      listener = onChange;
      return () => {
        listener = null;
      };
    },
    emit(hidden: boolean) {
      listener?.(hidden);
    },
  };
}

/** 실제 store/machine의 transition을 그대로 쓰는 테스트용 래퍼. */
function createTestMachine() {
  let state = transition(transition(createInitialMachineState(), "START_COUNTDOWN"), "START_RACE");
  return {
    isPaused: () => state.paused,
    dispatch: (event: GameEvent) => {
      state = transition(state, event);
    },
    getPhase: () => state.phase,
  };
}

function singleRunnerState(): RaceState {
  return createRaceState(
    [{ id: "a", stats: { speed: 60, stamina: 60, burst: 0, luck: 0 } }],
    createSeededRng(1),
  );
}

/** 선두(유일한 러너) 진행률을 임의로 지정한 상태. 슬로모션 트리거 여부를 통제하기 위해 쓴다. */
function singleRunnerStateAtProgress(progress: number): RaceState {
  const base = singleRunnerState();
  return {
    ...base,
    runners: base.runners.map((runner) => ({ ...runner, position: progress * TRACK_LENGTH })),
  };
}

describe("createRenderLoop", () => {
  it("주입한 raf 시간 소스로 여러 프레임을 진행하면 매 프레임 onFrame이 호출되고 시뮬레이션이 전진한다", () => {
    const raf = createManualRaf();
    const visibility = createManualVisibility();
    const machine = createTestMachine();
    let frameCount = 0;

    const loop = createRenderLoop(singleRunnerState(), {
      raf,
      visibility,
      machine,
      rng: createSeededRng(1),
      onFrame: () => {
        frameCount++;
      },
    });

    loop.start();
    [0, 16, 32, 48, 64].forEach((t) => raf.tick(t));

    expect(frameCount).toBe(5);
    expect(loop.getState().elapsedTime).toBeGreaterThan(0);
    expect(loop.getState().runners[0].position).toBeGreaterThan(0);
  });

  it("동일한 프레임 타임스탬프 시퀀스에서 결과가 결정적이다", () => {
    function run(): RaceState {
      const raf = createManualRaf();
      const visibility = createManualVisibility();
      const machine = createTestMachine();

      const loop = createRenderLoop(singleRunnerState(), {
        raf,
        visibility,
        machine,
        rng: createSeededRng(1),
        onFrame: () => {},
      });

      loop.start();
      [0, 16, 33, 50, 66, 83].forEach((t) => raf.tick(t));
      return loop.getState();
    }

    expect(run()).toEqual(run());
  });

  it("visibility hidden 통지 시 PAUSE로 전이하고 시뮬레이션이 멈추며, 복귀 시 RESUME하되 큰 dt 점프를 소비하지 않는다", () => {
    const raf = createManualRaf();
    const visibility = createManualVisibility();
    const machine = createTestMachine();
    const positions: number[] = [];

    const loop = createRenderLoop(singleRunnerState(), {
      raf,
      visibility,
      machine,
      rng: createSeededRng(1),
      onFrame: (state) => positions.push(state.runners[0].position),
    });

    loop.start();
    raf.tick(0); // 첫 프레임은 기준 시각만 설정하고 전진하지 않는다.
    raf.tick(1000); // 1초 경과 -> 전진.

    const positionBeforePause = positions[positions.length - 1];
    expect(positionBeforePause).toBeGreaterThan(0);
    expect(machine.getPhase()).toBe("racing");
    expect(machine.isPaused()).toBe(false);

    visibility.emit(true);
    expect(machine.isPaused()).toBe(true);

    raf.tick(6000); // hidden 동안 5초가 지나도 전진하지 않는다.
    expect(positions[positions.length - 1]).toBe(positionBeforePause);

    visibility.emit(false);
    expect(machine.isPaused()).toBe(false);

    raf.tick(6016); // 복귀 직후 프레임: hidden 동안의 큰 시간차를 dt로 소비하지 않는다.
    expect(positions[positions.length - 1]).toBe(positionBeforePause);

    raf.tick(6032); // 이후 정상 프레임 간격이면 다시 전진한다.
    expect(positions[positions.length - 1]).toBeGreaterThan(positionBeforePause);
  });

  it("stop() 호출 후에는 raf가 취소되어 더 이상 프레임이 소비되지 않는다", () => {
    const raf = createManualRaf();
    const visibility = createManualVisibility();
    const machine = createTestMachine();
    let frameCount = 0;

    const loop = createRenderLoop(singleRunnerState(), {
      raf,
      visibility,
      machine,
      rng: createSeededRng(1),
      onFrame: () => {
        frameCount++;
      },
    });

    loop.start();
    raf.tick(0);
    loop.stop();
    raf.tick(16); // pending 콜백이 취소되어 아무 일도 일어나지 않는다.

    expect(frameCount).toBe(1);
  });

  it("슬로모션 트리거 상태에서는 동일한 raf 타임스탬프 시퀀스에서 시뮬레이션 전진량(경과 시간)이 배율만큼 작다(T13)", () => {
    function elapsedAfterOneSecond(initialState: RaceState): number {
      const raf = createManualRaf();
      const visibility = createManualVisibility();
      const machine = createTestMachine();

      const loop = createRenderLoop(initialState, {
        raf,
        visibility,
        machine,
        rng: createSeededRng(1),
        onFrame: () => {},
      });

      loop.start();
      raf.tick(0); // 기준 시각만 설정.
      raf.tick(1000); // 1초 경과.
      return loop.getState().elapsedTime;
    }

    const normalElapsed = elapsedAfterOneSecond(singleRunnerStateAtProgress(0));
    const slowMotionElapsed = elapsedAfterOneSecond(singleRunnerStateAtProgress(0.95));

    expect(normalElapsed).toBeCloseTo(1, 1);
    expect(slowMotionElapsed).toBeCloseTo(1 * SLOW_MOTION_TIME_SCALE, 1);
    expect(slowMotionElapsed).toBeLessThan(normalElapsed * SLOW_MOTION_TIME_SCALE + 0.05);
  });
});
