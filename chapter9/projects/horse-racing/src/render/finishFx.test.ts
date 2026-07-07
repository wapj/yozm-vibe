import { describe, expect, it, vi } from "vitest";
import { computeSlowMotionTimeScale, drawFinishBanner, drawWinnerSpotlight } from "./finishFx";
import { createMockRenderContext as createMockCtx } from "./testing";
import { SLOW_MOTION_TIME_SCALE, WINNER_SPOTLIGHT_RADIUS } from "./types";
import type { RaceLayout, RenderContext, RunnerMeta } from "./types";
import { TRACK_LENGTH } from "../sim/types";
import type { RaceState, RunnerState } from "../sim/types";

function makeRunner(id: string, position: number): RunnerState {
  return {
    id,
    stats: { speed: 70, stamina: 70, burst: 70, luck: 50 },
    position,
    burstPhase: 0,
    skillId: "",
    skillActivated: false,
    skillActivatedAt: null,
  };
}

function makeState(positions: number[], finished: boolean): RaceState {
  return {
    runners: positions.map((position, index) => makeRunner(`horse-${index + 1}`, position)),
    elapsedTime: 10,
    finished,
  };
}

/**
 * 실제 CanvasRenderingContext2D의 save()/restore() 스택 동작을 흉내 내는 mock.
 * fillStyle·font 등 스타일 속성이 save() 시점에 스냅샷되고 restore() 시점에 복원되므로,
 * drawFinishBanner가 설정한 스타일이 restore 이후로 누수되지 않는지를 값으로 검증할 수 있다.
 */
function createStatefulMockCtx(): RenderContext {
  const ctx = createMockCtx();
  const stack: Array<{
    fillStyle: RenderContext["fillStyle"];
    font: string;
    textAlign: CanvasTextAlign;
    textBaseline: CanvasTextBaseline;
    globalAlpha: number;
  }> = [];

  ctx.save = vi.fn(() => {
    stack.push({
      fillStyle: ctx.fillStyle,
      font: ctx.font,
      textAlign: ctx.textAlign,
      textBaseline: ctx.textBaseline,
      globalAlpha: ctx.globalAlpha,
    });
  });
  ctx.restore = vi.fn(() => {
    const snapshot = stack.pop();
    if (!snapshot) return;
    ctx.fillStyle = snapshot.fillStyle;
    ctx.font = snapshot.font;
    ctx.textAlign = snapshot.textAlign;
    ctx.textBaseline = snapshot.textBaseline;
    ctx.globalAlpha = snapshot.globalAlpha;
  });

  return ctx;
}

const DIMENSIONS = { width: 800, height: 300 };

describe("computeSlowMotionTimeScale", () => {
  it("선두 진행률이 임계값 미만이면 1.0을 반환한다", () => {
    const state = makeState([TRACK_LENGTH * 0.85, TRACK_LENGTH * 0.7], false);
    expect(computeSlowMotionTimeScale(state, 0.9)).toBe(1.0);
  });

  it("선두 진행률이 임계값 이상이면 SLOW_MOTION_TIME_SCALE을 반환한다", () => {
    const state = makeState([TRACK_LENGTH * 0.95, TRACK_LENGTH * 0.5], false);
    expect(computeSlowMotionTimeScale(state, 0.9)).toBe(SLOW_MOTION_TIME_SCALE);
  });

  it("선두 진행률이 임계값과 정확히 같으면 SLOW_MOTION_TIME_SCALE을 반환한다(경계값)", () => {
    const state = makeState([TRACK_LENGTH * 0.9, TRACK_LENGTH * 0.5], false);
    expect(computeSlowMotionTimeScale(state, 0.9)).toBe(SLOW_MOTION_TIME_SCALE);
  });

  it("완주(finished=true) 후에도 선두 위치가 트랙 길이라 슬로모션이 유지된다(T8 REVIEW 메모 1 정책)", () => {
    const state = makeState([TRACK_LENGTH, TRACK_LENGTH - 10], true);
    expect(computeSlowMotionTimeScale(state)).toBe(SLOW_MOTION_TIME_SCALE);
  });
});

describe("drawFinishBanner", () => {
  const LAYOUT: RaceLayout = {
    runners: [
      { id: "horse-1", x: 100, y: 50 },
      { id: "horse-2", x: 200, y: 100 },
    ],
    leaderboard: [
      { id: "horse-1", rank: 1 },
      { id: "horse-2", rank: 2 },
    ],
  };

  const RUNNERS_META: RunnerMeta[] = [
    { id: "horse-1", number: 1, name: "번개질주", color: "#e63946" },
    { id: "horse-2", number: 2, name: "은빛바람", color: "#457b9d" },
  ];

  it("완주 + 접전(isPhotoFinish true)이면 포토 피니시 문구가 fillText로 노출된다", () => {
    const ctx = createMockCtx();
    const state = makeState([TRACK_LENGTH, TRACK_LENGTH - 5], true);

    drawFinishBanner(ctx, DIMENSIONS, LAYOUT, RUNNERS_META, state);

    expect(ctx.fillText).toHaveBeenCalledWith("포토 피니시!", DIMENSIONS.width / 2, DIMENSIONS.height / 2);
  });

  it("완주 + 접전이 아니면 우승마 번호·이름이 노출된다", () => {
    const ctx = createMockCtx();
    const state = makeState([TRACK_LENGTH, TRACK_LENGTH - 500], true);

    drawFinishBanner(ctx, DIMENSIONS, LAYOUT, RUNNERS_META, state);

    const texts = (ctx.fillText as ReturnType<typeof vi.fn>).mock.calls.map((call) => call[0] as string);
    expect(texts).toHaveLength(1);
    expect(texts[0]).toContain("1번");
    expect(texts[0]).toContain("번개질주");
  });

  it("미완주 상태에서는 결과 배너가 그려지지 않는다", () => {
    const ctx = createMockCtx();
    const state = makeState([TRACK_LENGTH * 0.95, TRACK_LENGTH * 0.5], false);

    drawFinishBanner(ctx, DIMENSIONS, LAYOUT, RUNNERS_META, state);

    expect(ctx.fillText).not.toHaveBeenCalled();
  });

  it("save()/restore()를 한 쌍씩 호출해 배너의 fillStyle·font 설정이 이후 그리기로 누수되지 않는다(T20a)", () => {
    const ctx = createStatefulMockCtx();
    ctx.fillStyle = "#123456";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "alphabetic";
    const state = makeState([TRACK_LENGTH, TRACK_LENGTH - 500], true);

    drawFinishBanner(ctx, DIMENSIONS, LAYOUT, RUNNERS_META, state);

    expect(ctx.save).toHaveBeenCalledTimes(1);
    expect(ctx.restore).toHaveBeenCalledTimes(1);
    expect(ctx.fillStyle).toBe("#123456");
    expect(ctx.font).toBe("10px sans-serif");
    expect(ctx.textAlign).toBe("left");
    expect(ctx.textBaseline).toBe("alphabetic");
  });

  it("포토 피니시 분기에서도 save()/restore()가 호출되어 이후 그리기로 상태가 누수되지 않는다", () => {
    const ctx = createStatefulMockCtx();
    ctx.fillStyle = "#abcdef";
    const state = makeState([TRACK_LENGTH, TRACK_LENGTH - 5], true);

    drawFinishBanner(ctx, DIMENSIONS, LAYOUT, RUNNERS_META, state);

    expect(ctx.save).toHaveBeenCalledTimes(1);
    expect(ctx.restore).toHaveBeenCalledTimes(1);
    expect(ctx.fillStyle).toBe("#abcdef");
  });
});

describe("drawWinnerSpotlight", () => {
  const LAYOUT: RaceLayout = {
    runners: [
      { id: "horse-1", x: 100, y: 50 },
      { id: "horse-2", x: 200, y: 100 },
    ],
    leaderboard: [
      { id: "horse-1", rank: 1 },
      { id: "horse-2", rank: 2 },
    ],
  };

  it("완주 상태에서 우승마(1위) layout 좌표를 중심으로 스포트라이트가 그려진다", () => {
    const ctx = createMockCtx();
    const state = makeState([TRACK_LENGTH, TRACK_LENGTH - 500], true);

    drawWinnerSpotlight(ctx, LAYOUT, state);

    expect(ctx.arc).toHaveBeenCalledWith(100, 50, WINNER_SPOTLIGHT_RADIUS, 0, Math.PI * 2);
    expect(ctx.save).toHaveBeenCalled();
    expect(ctx.restore).toHaveBeenCalled();
  });

  it("미완주 상태에서는 스포트라이트가 그려지지 않는다", () => {
    const ctx = createMockCtx();
    const state = makeState([TRACK_LENGTH * 0.95, TRACK_LENGTH * 0.5], false);

    drawWinnerSpotlight(ctx, LAYOUT, state);

    expect(ctx.arc).not.toHaveBeenCalled();
    expect(ctx.save).not.toHaveBeenCalled();
  });

  it("우승마가 layout.runners에 없으면(불일치) 예외 없이 건너뛴다", () => {
    const ctx = createMockCtx();
    const state = makeState([TRACK_LENGTH, TRACK_LENGTH - 500], true);
    const layoutMissingWinner: RaceLayout = {
      runners: [{ id: "horse-2", x: 200, y: 100 }],
      leaderboard: [
        { id: "horse-1", rank: 1 },
        { id: "horse-2", rank: 2 },
      ],
    };

    expect(() => drawWinnerSpotlight(ctx, layoutMissingWinner, state)).not.toThrow();
    expect(ctx.arc).not.toHaveBeenCalled();
  });
});
