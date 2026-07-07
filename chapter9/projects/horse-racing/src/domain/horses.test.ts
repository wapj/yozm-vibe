import { describe, expect, it } from "vitest";
import { createDefaultState, validateSavedState } from "../persistence/schema";
import { applyStatVariance } from "./stats";
import { estimateWinProbabilities } from "./odds";
import { createHorseCatalog, MIN_BASE_STAT } from "./horses";
import { STAT_KEYS } from "./types";

describe("createHorseCatalog", () => {
  it("각 말의 모든 스탯이 하한(> 0) 이상이다", () => {
    const catalog = createHorseCatalog(8);
    for (const horse of catalog) {
      for (const key of STAT_KEYS) {
        expect(horse.baseStats[key]).toBeGreaterThanOrEqual(MIN_BASE_STAT);
        expect(horse.baseStats[key]).toBeGreaterThan(0);
      }
    }
  });

  it("스탯 변동과 승률 추정에 넣어도 NaN이 발생하지 않는다", () => {
    const catalog = createHorseCatalog(8);
    const variedStatsList = catalog.map((horse) => applyStatVariance(horse.baseStats));

    for (const variedStats of variedStatsList) {
      for (const key of STAT_KEYS) {
        expect(Number.isNaN(variedStats[key])).toBe(false);
      }
    }

    const probabilities = estimateWinProbabilities(variedStatsList);
    for (const probability of probabilities) {
      expect(Number.isNaN(probability)).toBe(false);
    }
  });

  it("생성된 말 id가 고유하다", () => {
    const catalog = createHorseCatalog(8);
    const ids = catalog.map((horse) => horse.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("말 id를 키로 SavedState.records에 넣으면 validateSavedState를 통과한다", () => {
    const catalog = createHorseCatalog(5);
    const state = {
      ...createDefaultState(),
      records: Object.fromEntries(
        catalog.map((horse) => [horse.id, { racesRun: 0, wins: 0, recentResults: [] }]),
      ),
    };
    expect(validateSavedState(state)).not.toBeNull();
  });

  it("count가 범위를 벗어나면 1마리 이상, 템플릿 개수 이하로 클램프된다", () => {
    expect(createHorseCatalog(0).length).toBeGreaterThanOrEqual(1);
    expect(createHorseCatalog(100).length).toBeLessThanOrEqual(8);
  });
});
