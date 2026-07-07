import { describe, expect, it } from "vitest";
import { computeRaceLayout } from "./layout";
import { TRACK_LENGTH } from "../sim/types";
import type { RaceState, RunnerState } from "../sim/types";
import { HORSE_SHAPE_HEIGHT } from "./types";

function makeRunner(id: string, position: number): RunnerState {
  return {
    id,
    stats: { speed: 50, stamina: 50, burst: 50, luck: 50 },
    position,
    burstPhase: 0,
    skillId: "",
    skillActivated: false,
    skillActivatedAt: null,
  };
}

function makeState(runners: RunnerState[]): RaceState {
  return { runners, elapsedTime: 0, finished: false };
}

const DIMENSIONS = { width: 800, height: 300 };

describe("computeRaceLayout", () => {
  it("진행률 0은 출발선 x, 완주(진행률 1)는 결승선 x로 매핑되고 그 사이는 단조 증가한다", () => {
    const runners = [
      makeRunner("a", 0),
      makeRunner("b", TRACK_LENGTH * 0.25),
      makeRunner("c", TRACK_LENGTH * 0.5),
      makeRunner("d", TRACK_LENGTH),
    ];
    const layout = computeRaceLayout(makeState(runners), DIMENSIONS);
    const byId = new Map(layout.runners.map((r) => [r.id, r]));

    const marginX = DIMENSIONS.width * 0.05;
    expect(byId.get("a")!.x).toBeCloseTo(marginX);
    expect(byId.get("d")!.x).toBeCloseTo(DIMENSIONS.width - marginX);
    expect(byId.get("a")!.x).toBeLessThan(byId.get("b")!.x);
    expect(byId.get("b")!.x).toBeLessThan(byId.get("c")!.x);
    expect(byId.get("c")!.x).toBeLessThan(byId.get("d")!.x);
  });

  it("경계값(음수·트랙 길이 초과 position)도 출발선~결승선 범위 안으로 클램프된다", () => {
    const runners = [makeRunner("under", -50), makeRunner("over", TRACK_LENGTH + 200)];
    const layout = computeRaceLayout(makeState(runners), DIMENSIONS);
    const byId = new Map(layout.runners.map((r) => [r.id, r]));

    const marginX = DIMENSIONS.width * 0.05;
    expect(byId.get("under")!.x).toBeCloseTo(marginX);
    expect(byId.get("over")!.x).toBeCloseTo(DIMENSIONS.width - marginX);
  });

  it.each([4, 5, 6, 7, 8])("러너 수가 %i명이어도 레인 y가 겹치지 않게 배분된다", (count) => {
    const runners = Array.from({ length: count }, (_, index) => makeRunner(`h${index}`, 0));
    const layout = computeRaceLayout(makeState(runners), DIMENSIONS);

    const ys = layout.runners.map((r) => r.y).sort((a, b) => a - b);
    for (let i = 1; i < ys.length; i++) {
      expect(ys[i]).toBeGreaterThan(ys[i - 1]);
    }
    expect(ys[0]).toBeGreaterThanOrEqual(0);
    expect(ys[ys.length - 1]).toBeLessThanOrEqual(DIMENSIONS.height);
  });

  it("순위표 항목이 현재 순위 순서(1위부터)로 산출된다", () => {
    const runners = [makeRunner("a", 100), makeRunner("b", 300), makeRunner("c", 50)];
    const layout = computeRaceLayout(makeState(runners), DIMENSIONS);

    expect(layout.leaderboard.map((entry) => entry.id)).toEqual(["b", "a", "c"]);
    expect(layout.leaderboard.map((entry) => entry.rank)).toEqual([1, 2, 3]);
  });

  it("동률이면 순위표에서 같은 순위를 공유한다", () => {
    const runners = [makeRunner("a", 100), makeRunner("b", 100), makeRunner("c", 50)];
    const layout = computeRaceLayout(makeState(runners), DIMENSIONS);

    const ranksById = new Map(layout.leaderboard.map((entry) => [entry.id, entry.rank]));
    expect(ranksById.get("a")).toBe(1);
    expect(ranksById.get("b")).toBe(1);
    expect(ranksById.get("c")).toBe(3);
  });

  it.each([4, 5, 6, 7, 8])(
    "레인 밴드 폭이 말 도형 높이 이상이라 러너 %i마리에서도 인접 말 도형이 세로로 겹치지 않는다(T10 REVIEW 메모 1)",
    (count) => {
      const runners = Array.from({ length: count }, (_, index) => makeRunner(`h${index}`, 0));
      const layout = computeRaceLayout(makeState(runners), DIMENSIONS);

      const ys = layout.runners.map((r) => r.y).sort((a, b) => a - b);
      const bandWidth = ys[1] - ys[0];
      expect(bandWidth).toBeGreaterThanOrEqual(HORSE_SHAPE_HEIGHT);
    },
  );
});
