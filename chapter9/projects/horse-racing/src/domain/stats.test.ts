import { describe, expect, it } from "vitest";
import {
  VARIANCE_RATIO,
  applyStatVariance,
  getConditionLevel,
  randomVarianceFactor,
} from "./stats";
import type { Stats } from "./types";

const baseStats: Stats = { speed: 100, stamina: 80, burst: 60, luck: 40 };

describe("randomVarianceFactor", () => {
  it("rng 결과에 비례해 ±10% 범위의 배율을 반환한다", () => {
    expect(randomVarianceFactor(() => 0)).toBeCloseTo(1 - VARIANCE_RATIO);
    expect(randomVarianceFactor(() => 0.5)).toBeCloseTo(1);
    expect(randomVarianceFactor(() => 1)).toBeCloseTo(1 + VARIANCE_RATIO);
  });
});

describe("applyStatVariance", () => {
  it("각 스탯 변동 결과가 기준값의 ±10% 범위 내에 있다 (경계값 포함)", () => {
    const lower = applyStatVariance(baseStats, () => 0);
    const upper = applyStatVariance(baseStats, () => 1);

    for (const key of Object.keys(baseStats) as (keyof Stats)[]) {
      expect(lower[key]).toBeCloseTo(baseStats[key] * 0.9);
      expect(upper[key]).toBeCloseTo(baseStats[key] * 1.1);
    }
  });

  it("무작위 rng를 여러 번 적용해도 항상 ±10% 범위 내에 머문다", () => {
    for (let i = 0; i < 200; i++) {
      const varied = applyStatVariance(baseStats);
      for (const key of Object.keys(baseStats) as (keyof Stats)[]) {
        const min = baseStats[key] * (1 - VARIANCE_RATIO);
        const max = baseStats[key] * (1 + VARIANCE_RATIO);
        expect(varied[key]).toBeGreaterThanOrEqual(min);
        expect(varied[key]).toBeLessThanOrEqual(max);
      }
    }
  });
});

describe("getConditionLevel", () => {
  it("변동이 없으면 보통 등급을 반환한다", () => {
    expect(getConditionLevel(baseStats, baseStats)).toBe("보통");
  });

  it("최저 변동(-10%)은 최하 등급을 반환한다", () => {
    const worst = applyStatVariance(baseStats, () => 0);
    expect(getConditionLevel(baseStats, worst)).toBe("최하");
  });

  it("최고 변동(+10%)은 최상 등급을 반환한다", () => {
    const best = applyStatVariance(baseStats, () => 1);
    expect(getConditionLevel(baseStats, best)).toBe("최상");
  });
});
