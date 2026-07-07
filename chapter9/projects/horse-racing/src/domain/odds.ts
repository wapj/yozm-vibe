import type { Stats } from "./types";

const STAT_WEIGHTS: Record<keyof Stats, number> = {
  speed: 0.4,
  stamina: 0.25,
  burst: 0.25,
  luck: 0.1,
};

export const DEFAULT_HOUSE_COEFFICIENT = 0.9;

/** 스탯을 가중합하여 경주력 점수를 산출한다. */
export function computeHorsePower(stats: Stats): number {
  return (
    stats.speed * STAT_WEIGHTS.speed +
    stats.stamina * STAT_WEIGHTS.stamina +
    stats.burst * STAT_WEIGHTS.burst +
    stats.luck * STAT_WEIGHTS.luck
  );
}

/** 출전마들의 경주력 점수를 정규화하여 합이 1이 되는 추정승률을 반환한다. */
export function estimateWinProbabilities(statsList: Stats[]): number[] {
  if (statsList.length === 0) return [];
  const powers = statsList.map(computeHorsePower);
  const total = powers.reduce((sum, power) => sum + power, 0);
  return powers.map((power) => power / total);
}

/** 배당률 = 1 / 추정승률 × 하우스계수 */
export function calculateOdds(
  winProbabilities: number[],
  houseCoefficient: number = DEFAULT_HOUSE_COEFFICIENT,
): number[] {
  return winProbabilities.map((probability) => (1 / probability) * houseCoefficient);
}
