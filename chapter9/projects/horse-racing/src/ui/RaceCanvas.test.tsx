import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createHorseCatalog } from "../domain/horses";
import { createRaceState } from "../sim/engine";
import { createSeededRng } from "../sim/rng";
import { createInitialMachineState, transition, type GameEvent } from "../store/machine";
import { createMockRenderContext } from "../render/testing";
import type { RafSource, RenderContext, VisibilitySource } from "../render/types";
import { RaceCanvas } from "./RaceCanvas";

afterEach(cleanup);

/** loop.test.ts와 동일한 가짜 raf: 테스트가 프레임 타임스탬프를 직접 통제한다. */
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

/** loop.test.ts와 동일한 가짜 visibility 소스: 단일 리스너만 유지한다(실제 subscribe 계약과 동일). */
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

/** loop.test.ts와 동일한 실제 store/machine 기반 테스트용 상태 머신. */
function createTestMachine() {
  let state = transition(transition(createInitialMachineState(), "START_COUNTDOWN"), "START_RACE");
  return {
    isPaused: () => state.paused,
    dispatch: (event: GameEvent) => {
      state = transition(state, event);
    },
  };
}

const createMockCtx = createMockRenderContext;

/** 프레임 진행 여부를 검증하기 위한 그리기 호출 수 스냅샷. 프레임당 정확한 호출 수에 의존하지 않는다. */
function drawCallCount(ctx: RenderContext): number {
  return (ctx.fillRect as ReturnType<typeof vi.fn>).mock.calls.length;
}

const HORSES = createHorseCatalog(2);

function initialState() {
  return createRaceState(
    HORSES.map((horse) => ({ id: horse.id, stats: horse.baseStats, skillId: horse.skill.id })),
    createSeededRng(1),
  );
}

describe("RaceCanvas", () => {
  it("mock ctx·가짜 raf로 마운트한 뒤 프레임을 진행시키면 renderScene(→mock ctx 그리기)이 호출된다", () => {
    const ctx = createMockCtx();
    const raf = createManualRaf();
    const visibility = createManualVisibility();
    const machine = createTestMachine();

    render(
      <RaceCanvas
        initialState={initialState()}
        horses={HORSES}
        machine={machine}
        getContext={() => ctx}
        raf={raf}
        visibility={visibility}
        rng={createSeededRng(1)}
      />,
    );

    expect(ctx.fillRect).not.toHaveBeenCalled();

    raf.tick(0);
    const afterFirstFrame = drawCallCount(ctx);
    expect(afterFirstFrame).toBeGreaterThan(0); // drawTrack 등 배경 그리기가 호출된다.
    // drawRunners: 러너 수만큼 좌표 이동(translate)이 발생한다(셰이크용 이동 포함 그 이상).
    const translateCalls = (ctx.translate as ReturnType<typeof vi.fn>).mock.calls;
    expect(translateCalls.length).toBeGreaterThanOrEqual(HORSES.length);

    raf.tick(16);
    expect(drawCallCount(ctx)).toBeGreaterThan(afterFirstFrame); // 다음 프레임도 그린다.
  });

  it("언마운트 시 loop.stop()으로 raf가 취소되고 그리기가 멎는다", () => {
    const ctx = createMockCtx();
    const raf = createManualRaf();
    const visibility = createManualVisibility();
    const machine = createTestMachine();

    const { unmount } = render(
      <RaceCanvas
        initialState={initialState()}
        horses={HORSES}
        machine={machine}
        getContext={() => ctx}
        raf={raf}
        visibility={visibility}
        rng={createSeededRng(1)}
      />,
    );

    raf.tick(0);
    const afterFirstFrame = drawCallCount(ctx);
    expect(afterFirstFrame).toBeGreaterThan(0);

    unmount();
    raf.tick(16); // pending 콜백이 취소되어 있으므로 아무 일도 일어나지 않는다.

    expect(drawCallCount(ctx)).toBe(afterFirstFrame);
  });

  it("hidden 프레임 렌더 정책(유지): 탭이 비활성화된 동안에도 매 프레임 계속 그린다", () => {
    const ctx = createMockCtx();
    const raf = createManualRaf();
    const visibility = createManualVisibility();
    const machine = createTestMachine();

    render(
      <RaceCanvas
        initialState={initialState()}
        horses={HORSES}
        machine={machine}
        getContext={() => ctx}
        raf={raf}
        visibility={visibility}
        rng={createSeededRng(1)}
      />,
    );

    raf.tick(0);
    const afterFirstFrame = drawCallCount(ctx);
    expect(afterFirstFrame).toBeGreaterThan(0);

    visibility.emit(true); // 탭 비활성화 -> 시뮬레이션은 멈추지만 그리기는 유지 정책.
    expect(machine.isPaused()).toBe(true);

    raf.tick(16);
    const afterHiddenFrame = drawCallCount(ctx);
    expect(afterHiddenFrame).toBeGreaterThan(afterFirstFrame); // hidden 중에도 onFrame이 호출되어 계속 그려진다.

    raf.tick(32);
    expect(drawCallCount(ctx)).toBeGreaterThan(afterHiddenFrame);
  });

  it("onFrame 콜백이 매 프레임 상태·순위와 함께 호출된다", () => {
    const ctx = createMockCtx();
    const raf = createManualRaf();
    const visibility = createManualVisibility();
    const machine = createTestMachine();
    const onFrame = vi.fn();

    render(
      <RaceCanvas
        initialState={initialState()}
        horses={HORSES}
        machine={machine}
        getContext={() => ctx}
        raf={raf}
        visibility={visibility}
        rng={createSeededRng(1)}
        onFrame={onFrame}
      />,
    );

    raf.tick(0);
    expect(onFrame).toHaveBeenCalledTimes(1);
    const [state, rankings] = onFrame.mock.calls[0];
    expect(state.runners).toHaveLength(HORSES.length);
    expect(rankings).toHaveLength(HORSES.length);

    raf.tick(16);
    expect(onFrame).toHaveBeenCalledTimes(2);
  });

  it("onFrame이 바뀌어도(참조 불안정) loop을 재시작하지 않는다", () => {
    const ctx = createMockCtx();
    const raf = createManualRaf();
    const visibility = createManualVisibility();
    const machine = createTestMachine();
    const state = initialState();

    const { rerender } = render(
      <RaceCanvas
        initialState={state}
        horses={HORSES}
        machine={machine}
        getContext={() => ctx}
        raf={raf}
        visibility={visibility}
        rng={createSeededRng(1)}
        onFrame={() => {}}
      />,
    );

    raf.tick(0);
    const afterFirstFrame = drawCallCount(ctx);
    expect(afterFirstFrame).toBeGreaterThan(0);

    const secondOnFrame = vi.fn();
    rerender(
      <RaceCanvas
        initialState={state}
        horses={HORSES}
        machine={machine}
        getContext={() => ctx}
        raf={raf}
        visibility={visibility}
        rng={createSeededRng(1)}
        onFrame={secondOnFrame}
      />,
    );

    raf.tick(16);
    expect(drawCallCount(ctx)).toBeGreaterThan(afterFirstFrame); // 재시작이라면 raf.request가 다시 걸려 pending이 남지 않는다.
    expect(secondOnFrame).toHaveBeenCalledTimes(1); // ref로 최신 콜백을 참조해 새 콜백이 호출된다.
  });
});
