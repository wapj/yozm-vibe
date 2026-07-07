import { STAT_KEYS, type ConditionLevel, type Stats } from "./types";

export const VARIANCE_RATIO = 0.1;

const CONDITION_LEVELS: ConditionLevel[] = ["최하", "부진", "보통", "호조", "최상"];

export function randomVarianceFactor(rng: () => number = Math.random): number {
  return 1 + (rng() * 2 - 1) * VARIANCE_RATIO;
}

/** 각 스탯에 ±10% 내외의 랜덤 변동을 적용한 회차별 스탯을 반환한다. */
export function applyStatVariance(
  baseStats: Stats,
  rng: () => number = Math.random,
): Stats {
  const varied = {} as Stats;
  for (const key of STAT_KEYS) {
    varied[key] = baseStats[key] * randomVarianceFactor(rng);
  }
  return varied;
}

export function averageVarianceRatio(baseStats: Stats, variedStats: Stats): number {
  const ratios = STAT_KEYS.map(
    (key) => (variedStats[key] - baseStats[key]) / baseStats[key],
  );
  return ratios.reduce((sum, ratio) => sum + ratio, 0) / ratios.length;
}

/** 기준 스탯 대비 변동 폭을 5단계 컨디션 지표로 변환한다. */
export function getConditionLevel(baseStats: Stats, variedStats: Stats): ConditionLevel {
  const ratio = averageVarianceRatio(baseStats, variedStats);
  const bandWidth = (VARIANCE_RATIO * 2) / CONDITION_LEVELS.length;
  const index = Math.min(
    CONDITION_LEVELS.length - 1,
    Math.max(0, Math.floor((ratio + VARIANCE_RATIO) / bandWidth)),
  );
  return CONDITION_LEVELS[index];
}
