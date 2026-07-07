import { describe, expect, it, vi } from "vitest";
import {
  computeTrackBounds,
  computeTrackGeometry,
  drawLeaderboard,
  drawRunners,
  drawTrack,
  renderRace,
  shadeColor,
} from "./renderer";
import { createMockRenderContext } from "./testing";
import type { RaceLayout, RunnerMeta } from "./types";

const DIMENSIONS = { width: 800, height: 300 };

const LAYOUT: RaceLayout = {
  runners: [
    { id: "a", x: 100, y: 50 },
    { id: "b", x: 200, y: 100 },
  ],
  leaderboard: [
    { id: "b", rank: 1 },
    { id: "a", rank: 2 },
  ],
  laneHeight: 34,
};

const RUNNERS_META: RunnerMeta[] = [
  { id: "a", number: 1, name: "번개질주", color: "#e63946" },
  { id: "b", number: 2, name: "은빛바람", color: "#457b9d" },
];

describe("shadeColor", () => {
  it("양수 amount는 밝게, 음수 amount는 어둡게 섞는다", () => {
    expect(shadeColor("#000000", 1)).toBe("#ffffff");
    expect(shadeColor("#ffffff", -1)).toBe("#000000");
    expect(shadeColor("#804020", 0)).toBe("#804020");
  });

  it("#rgb 축약형을 처리하고, 잘못된 hex는 원본을 그대로 반환한다", () => {
    expect(shadeColor("#fff", -1)).toBe("#000000");
    expect(shadeColor("not-a-color", 0.5)).toBe("not-a-color");
  });
});

describe("트랙 렌더", () => {
  it("출발선 x가 결승선 x보다 작고, 지오메트리 밴드가 위에서 아래로 정렬된다", () => {
    const bounds = computeTrackBounds(DIMENSIONS);
    expect(bounds.startX).toBeLessThan(bounds.finishX);

    const geometry = computeTrackGeometry(DIMENSIONS);
    expect(geometry.skyBottom).toBeLessThan(geometry.standBottom);
    expect(geometry.standBottom).toBeLessThan(geometry.trackTop);
    expect(geometry.trackTop).toBeLessThan(geometry.trackBottom);
    expect(geometry.trackBottom).toBeLessThanOrEqual(DIMENSIONS.height);
  });

  it("하늘·관중석·주로 배경과 START/FINISH 표지가 그려진다", () => {
    const ctx = createMockRenderContext();
    drawTrack(ctx, DIMENSIONS);

    expect(ctx.fillRect).toHaveBeenCalled();
    expect(ctx.createLinearGradient).toHaveBeenCalled();

    const texts = (ctx.fillText as ReturnType<typeof vi.fn>).mock.calls.map((call) => call[0] as string);
    expect(texts).toContain("START");
    expect(texts).toContain("FINISH");
  });

  it("laneCount를 넘기면 레인 구분선이 laneCount-1개 그려진다(setLineDash 사용)", () => {
    const ctx = createMockRenderContext();
    drawTrack(ctx, DIMENSIONS, { laneCount: 4 });

    expect(ctx.setLineDash).toHaveBeenCalled();
    const geometry = computeTrackGeometry(DIMENSIONS);
    const laneHeight = (geometry.trackBottom - geometry.trackTop) / 4;
    const moveToYs = (ctx.moveTo as ReturnType<typeof vi.fn>).mock.calls.map((call) => call[1] as number);
    for (let lane = 1; lane < 4; lane += 1) {
      expect(moveToYs).toContain(geometry.trackTop + laneHeight * lane);
    }
  });
});

describe("말 렌더(갤럽 모션 포함)", () => {
  it("각 러너가 layout의 (x, y) 좌표로 이동(translate)되어 그려진다", () => {
    const ctx = createMockRenderContext();
    drawRunners(ctx, LAYOUT, RUNNERS_META, 0);

    const translateCalls = (ctx.translate as ReturnType<typeof vi.fn>).mock.calls;
    expect(translateCalls).toContainEqual([100, 50]);
    expect(translateCalls).toContainEqual([200, 100]);
  });

  it("다리 모션이 프레임(시간)에 따라 달라진다(정지 화면이 아니다)", () => {
    const ctxAtT0 = createMockRenderContext();
    drawRunners(ctxAtT0, LAYOUT, RUNNERS_META, 0);
    const legsAtT0 = (ctxAtT0.quadraticCurveTo as ReturnType<typeof vi.fn>).mock.calls;

    const ctxAtT1 = createMockRenderContext();
    drawRunners(ctxAtT1, LAYOUT, RUNNERS_META, 0.3);
    const legsAtT1 = (ctxAtT1.quadraticCurveTo as ReturnType<typeof vi.fn>).mock.calls;

    expect(legsAtT0).not.toEqual(legsAtT1);
  });

  it("완주(finished) 후에는 정지 자세로 전환되어 시간이 흘러도 다리 모션이 같다", () => {
    const ctxAtT0 = createMockRenderContext();
    drawRunners(ctxAtT0, LAYOUT, RUNNERS_META, 0, { finished: true });
    const legsAtT0 = (ctxAtT0.quadraticCurveTo as ReturnType<typeof vi.fn>).mock.calls;

    const ctxAtT1 = createMockRenderContext();
    drawRunners(ctxAtT1, LAYOUT, RUNNERS_META, 0.3, { finished: true });
    const legsAtT1 = (ctxAtT1.quadraticCurveTo as ReturnType<typeof vi.fn>).mock.calls;

    expect(legsAtT0).toEqual(legsAtT1);
  });

  it("말 번호가 안장보에 그려져 색상 외 식별 수단을 제공한다", () => {
    const ctx = createMockRenderContext();
    drawRunners(ctx, LAYOUT, RUNNERS_META, 0);

    const texts = (ctx.fillText as ReturnType<typeof vi.fn>).mock.calls.map((call) => call[0] as string);
    expect(texts).toContain("1");
    expect(texts).toContain("2");
  });
});

describe("순위표 렌더 + 번호·이름 병기", () => {
  it("leaderboard 순서대로 항목이 그려지고, 각 말에 번호와 이름 텍스트가 함께 노출된다", () => {
    const ctx = createMockRenderContext();
    drawLeaderboard(ctx, LAYOUT, RUNNERS_META);

    const texts = (ctx.fillText as ReturnType<typeof vi.fn>).mock.calls.map((call) => call[0] as string);
    expect(texts).toContain("2번 은빛바람");
    expect(texts).toContain("1번 번개질주");
    // 1위(은빛바람) 라벨이 2위(번개질주) 라벨보다 먼저 그려진다.
    expect(texts.indexOf("2번 은빛바람")).toBeLessThan(texts.indexOf("1번 번개질주"));
  });
});

describe("renderRace", () => {
  it("트랙·말·순위표를 한 프레임 분 그린다", () => {
    const ctx = createMockRenderContext();
    renderRace(ctx, DIMENSIONS, LAYOUT, RUNNERS_META, 0.1);

    expect(ctx.fillRect).toHaveBeenCalled();
    const translateCalls = (ctx.translate as ReturnType<typeof vi.fn>).mock.calls;
    expect(translateCalls).toContainEqual([100, 50]);
    expect(translateCalls).toContainEqual([200, 100]);

    const texts = (ctx.fillText as ReturnType<typeof vi.fn>).mock.calls.map((call) => call[0] as string);
    expect(texts).toContain("2번 은빛바람");
  });
});

describe("폴백 분기(T11 REVIEW 메모 1)", () => {
  it("drawRunners: runnersMeta에 없는 id는 기본색으로 예외 없이 그려진다", () => {
    const ctx = createMockRenderContext();
    expect(() => drawRunners(ctx, LAYOUT, [], 0)).not.toThrow();

    const translateCalls = (ctx.translate as ReturnType<typeof vi.fn>).mock.calls;
    expect(translateCalls).toContainEqual([100, 50]);
    expect(translateCalls).toContainEqual([200, 100]);
  });

  it("drawLeaderboard: meta가 없는 러너는 순위 숫자만으로 예외 없이 그려진다", () => {
    const ctx = createMockRenderContext();
    expect(() => drawLeaderboard(ctx, LAYOUT, [])).not.toThrow();

    const texts = (ctx.fillText as ReturnType<typeof vi.fn>).mock.calls.map((call) => call[0] as string);
    expect(texts).toEqual(["1", "2"]);
  });
});
