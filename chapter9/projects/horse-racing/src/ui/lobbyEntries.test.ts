import { describe, expect, it } from "vitest";
import { calculateOdds, estimateWinProbabilities } from "../domain/odds";
import type { HorseProfile, RaceRecord } from "../domain/types";
import {
  WIN_STREAK_BADGE_THRESHOLD,
  buildLobbyEntries,
  computeWinStreak,
  hasWinStreakBadge,
} from "./lobbyEntries";

function createHorse(id: string, number: number, statValue: number): HorseProfile {
  return {
    id,
    number,
    name: `말${number}`,
    color: "#000000",
    personality: "테스트",
    baseStats: { speed: statValue, stamina: statValue, burst: statValue, luck: statValue },
    skill: { id: "start-dash", name: "스타트 대시", description: "" },
  };
}

/** rng()*2-1 == 0이 되어 randomVarianceFactor가 정확히 1이 되는 상수 rng (변동 없는 스냅샷). */
function noVarianceRng(): () => number {
  return () => 0.5;
}

describe("buildLobbyEntries", () => {
  const strong = createHorse("horse-1", 1, 90);
  const weak = createHorse("horse-2", 2, 40);
  const catalog = [strong, weak];

  it("동일 rng 시퀀스로 같은 카탈로그·records를 조립하면 같은 currentStats·odds가 나온다", () => {
    const first = buildLobbyEntries(catalog, {}, noVarianceRng());
    const second = buildLobbyEntries(catalog, {}, noVarianceRng());

    expect(first.map((entry) => entry.currentStats)).toEqual(second.map((entry) => entry.currentStats));
    expect(first.map((entry) => entry.odds)).toEqual(second.map((entry) => entry.odds));
  });

  it("배당률이 calculateOdds 결과와 일치하고 약체가 강자보다 고배당이다", () => {
    const entries = buildLobbyEntries(catalog, {}, noVarianceRng());

    const expectedProbabilities = estimateWinProbabilities(catalog.map((horse) => horse.baseStats));
    const expectedOdds = calculateOdds(expectedProbabilities);

    entries.forEach((entry, index) => {
      expect(entry.odds).toBeCloseTo(expectedOdds[index]);
    });
    expect(entries[1].odds).toBeGreaterThan(entries[0].odds);
  });

  it("records에 해당 말 키가 없으면 빈 전적으로 조립된다", () => {
    const entries = buildLobbyEntries(catalog, {}, noVarianceRng());

    expect(entries[0].record).toEqual({ racesRun: 0, wins: 0, recentResults: [] });
  });

  it("저장된 records가 있으면 그대로 반영된다", () => {
    const records: Record<string, RaceRecord> = {
      "horse-1": { racesRun: 5, wins: 3, recentResults: [1, 1, 2, 3, 1] },
    };
    const entries = buildLobbyEntries(catalog, records, noVarianceRng());

    expect(entries[0].record).toEqual(records["horse-1"]);
  });
});

describe("computeWinStreak / hasWinStreakBadge", () => {
  it("recentResults가 [1,1,3,...]이면 연속 1위 2회로 연승 판정된다", () => {
    expect(computeWinStreak([1, 1, 3, 2, 1])).toBe(2);
    expect(hasWinStreakBadge([1, 1, 3, 2, 1])).toBe(true);
  });

  it("recentResults가 [3,1,1,...]이면 최신이 1위가 아니라 연승이 아니다", () => {
    expect(computeWinStreak([3, 1, 1])).toBe(0);
    expect(hasWinStreakBadge([3, 1, 1])).toBe(false);
  });

  it("빈 전적(racesRun=0)에서 예외 없이 비연승으로 처리된다", () => {
    expect(computeWinStreak([])).toBe(0);
    expect(hasWinStreakBadge([])).toBe(false);
  });

  it("연승 배지 임계값은 연속 1위 2회 이상이다", () => {
    expect(WIN_STREAK_BADGE_THRESHOLD).toBe(2);
  });
});
