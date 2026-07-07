import { calculateOdds, estimateWinProbabilities } from "../domain/odds";
import { applyStatVariance, getConditionLevel } from "../domain/stats";
import type { HorseProfile, HorseRaceEntry, RaceRecord } from "../domain/types";

const EMPTY_RECORD: RaceRecord = { racesRun: 0, wins: 0, recentResults: [] };

/** PRD 4.7의 "연승"에 대응하는 배지 임계값. 연속 1위 2회 이상을 연승으로 판정한다(가장 단순한 기준, 되돌리기 쉬운 구현 결정). */
export const WIN_STREAK_BADGE_THRESHOLD = 2;

/** recentResults(최신이 앞)에서 맨 앞부터 끊기지 않고 이어지는 1위 횟수를 센다. */
export function computeWinStreak(recentResults: number[]): number {
  let streak = 0;
  for (const rank of recentResults) {
    if (rank !== 1) break;
    streak += 1;
  }
  return streak;
}

export function hasWinStreakBadge(recentResults: number[]): boolean {
  return computeWinStreak(recentResults) >= WIN_STREAK_BADGE_THRESHOLD;
}

/**
 * 출전마 카탈로그·저장 전적·주입 rng로 로비에 표시할 `HorseRaceEntry[]`를 조립한다.
 * 회차 변동은 주입 rng로 1회만 적용한 스냅샷을 반환하는 순수 함수다(다시 굴리는 배선은
 * 로비 오케스트레이션의 몫). `src/domain`과 rng에만 의존하며 `src/sim`·`src/store`를
 * 참조하지 않는다.
 */
export function buildLobbyEntries(
  catalog: HorseProfile[],
  records: Record<string, RaceRecord>,
  rng: () => number = Math.random,
): HorseRaceEntry[] {
  const currentStatsList = catalog.map((horse) => applyStatVariance(horse.baseStats, rng));
  const winProbabilities = estimateWinProbabilities(currentStatsList);
  const oddsList = calculateOdds(winProbabilities);

  return catalog.map((horse, index) => ({
    horse,
    currentStats: currentStatsList[index],
    condition: getConditionLevel(horse.baseStats, currentStatsList[index]),
    winProbability: winProbabilities[index],
    odds: oddsList[index],
    record: records[horse.id] ?? EMPTY_RECORD,
  }));
}
