/**
 * 주입 가능한 raf·visibility 소스 위에서 도는 렌더 루프 오케스트레이터(T10).
 * 매 프레임 실제 dt를 T9 accumulator(advanceWithAccumulator)에 넘겨 시뮬레이션을
 * 전진시키고, 그리기는 콜백(onFrame)으로 트리거해 React 리렌더와 분리한다.
 * 탭 비활성화(visibility hidden) 시 상태 머신을 PAUSE로 전이하고 시뮬레이션 전진을
 * 멈추며, 복귀 시 RESUME으로 전이하되 hidden 동안 누적된 실제 시간 차를 dt로
 * 소비하지 않도록(큰 점프 방지) lastTime을 재동기화한다. 선두가 결승선에 근접하면
 * (`isSlowMotionTriggered`, T13) accumulator에 넘기는 dt에 슬로모션 배율을 곱해
 * 시뮬레이션 전진 속도를 늦춘다.
 */
import { advanceWithAccumulator, createAccumulator, FIXED_SUBSTEP } from "../sim/driver";
import { rankRunners } from "../sim/engine";
import type { RaceState } from "../sim/types";
import { computeSlowMotionTimeScale } from "./finishFx";
import type { RenderLoop, RenderLoopOptions } from "./types";

export function createRenderLoop(initialState: RaceState, options: RenderLoopOptions): RenderLoop {
  const rng = options.rng ?? Math.random;
  const fixedStep = options.fixedStep ?? FIXED_SUBSTEP;

  let raceState = initialState;
  let accumulator = createAccumulator();
  /** 직전 프레임의 raf 타임스탬프. null이면 다음 프레임은 dt를 소비하지 않고 기준점만 다시 잡는다. */
  let lastTime: number | null = null;
  let hidden = false;
  let running = false;
  let rafHandle: number | null = null;
  let unsubscribeVisibility: (() => void) | null = null;

  function handleVisibilityChange(nextHidden: boolean): void {
    hidden = nextHidden;
    if (hidden) {
      if (!options.machine.isPaused()) options.machine.dispatch("PAUSE");
    } else if (options.machine.isPaused()) {
      options.machine.dispatch("RESUME");
    }
    // hidden 전환·복귀 양쪽 모두 다음 프레임이 dt를 소비하지 않고 기준점만 다시 잡게 한다.
    lastTime = null;
  }

  function frame(timeMs: number): void {
    if (!running) return;

    /** 이번 프레임의 시각 효과용 dt(슬로모션 배율 적용). 완주 후 elapsedTime이 고정되어도 파티클이 움직이게 한다. */
    let frameDt = 0;
    if (!hidden) {
      if (lastTime !== null) {
        const rawDt = Math.max(0, (timeMs - lastTime) / 1000);
        const timeScale = computeSlowMotionTimeScale(raceState);
        frameDt = rawDt * timeScale;
        const advanced = advanceWithAccumulator(raceState, accumulator, frameDt, rng, fixedStep);
        raceState = advanced.state;
        accumulator = advanced.accumulator;
      }
      lastTime = timeMs;
    }

    options.onFrame(raceState, rankRunners(raceState.runners), frameDt);
    rafHandle = options.raf.request(frame);
  }

  return {
    start() {
      running = true;
      lastTime = null;
      hidden = false;
      unsubscribeVisibility = options.visibility.subscribe(handleVisibilityChange);
      rafHandle = options.raf.request(frame);
    },
    stop() {
      running = false;
      if (rafHandle !== null) options.raf.cancel(rafHandle);
      unsubscribeVisibility?.();
      unsubscribeVisibility = null;
    },
    getState() {
      return raceState;
    },
  };
}
