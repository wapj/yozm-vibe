import { describe, expect, it } from "vitest";
import {
  DEFAULT_HOUSE_COEFFICIENT,
  calculateOdds,
  estimateWinProbabilities,
} from "./odds";
import type { Stats } from "./types";

const statsList: Stats[] = [
  { speed: 120, stamina: 100, burst: 90, luck: 60 }, // 강자
  { speed: 100, stamina: 90, burst: 80, luck: 50 },
  { speed: 80, stamina: 70, burst: 60, luck: 40 },
  { speed: 60, stamina: 50, burst: 40, luck: 30 }, // 약체
];

describe("estimateWinProbabilities", () => {
  it("모든 말의 추정승률 합이 1로 정규화된다", () => {
    const probabilities = estimateWinProbabilities(statsList);
    const total = probabilities.reduce((sum, p) => sum + p, 0);
    expect(total).toBeCloseTo(1);
  });

  it("스탯이 우세한 말일수록 추정승률이 높다", () => {
    const probabilities = estimateWinProbabilities(statsList);
    for (let i = 0; i < probabilities.length - 1; i++) {
      expect(probabilities[i]).toBeGreaterThan(probabilities[i + 1]);
    }
  });

  it("빈 목록이면 빈 배열을 반환한다", () => {
    expect(estimateWinProbabilities([])).toEqual([]);
  });
});

describe("calculateOdds", () => {
  it("배당률이 1 / 추정승률 × 하우스계수 규칙을 따른다", () => {
    const probabilities = estimateWinProbabilities(statsList);
    const odds = calculateOdds(probabilities);
    probabilities.forEach((p, i) => {
      expect(odds[i]).toBeCloseTo((1 / p) * DEFAULT_HOUSE_COEFFICIENT);
    });
  });

  it("하우스계수를 직접 지정할 수 있다", () => {
    const probabilities = estimateWinProbabilities(statsList);
    const odds = calculateOdds(probabilities, 0.8);
    probabilities.forEach((p, i) => {
      expect(odds[i]).toBeCloseTo((1 / p) * 0.8);
    });
  });

  it("추정승률이 높은 말일수록 배당률이 낮다", () => {
    const probabilities = estimateWinProbabilities(statsList);
    const odds = calculateOdds(probabilities);
    for (let i = 0; i < odds.length - 1; i++) {
      expect(odds[i]).toBeLessThan(odds[i + 1]);
    }
  });
});
