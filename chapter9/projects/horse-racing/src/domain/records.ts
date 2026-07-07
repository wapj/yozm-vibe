import type { RaceRecord } from "./types";

/** PRD 4.7: 말 카드에 "최근 5경기 성적"을 노출하므로 유지 개수를 5로 고정한다. */
export const RECENT_RESULTS_LIMIT = 5;

/** 완주 순위 입력. `src/sim`의 `RankedRunner`가 구조적으로 이 형태를 만족한다(id·rank만 사용). */
export interface RaceResultEntry {
  id: string;
  rank: number;
}

/**
 * 완주 순위로 말별 `RaceRecord`를 갱신한 새 records를 반환한다(입력 불변, 방어 복사).
 * 순위에 없던 말 키는 건드리지 않고, 순위에 있는 말은 신규 출전이면 새로 생성한다.
 */
export function updateRecordsWithRaceResult(
  records: Record<string, RaceRecord>,
  results: RaceResultEntry[],
): Record<string, RaceRecord> {
  const updated = { ...records };

  for (const { id, rank } of results) {
    const existing = updated[id];
    const racesRun = (existing?.racesRun ?? 0) + 1;
    const wins = (existing?.wins ?? 0) + (rank === 1 ? 1 : 0);
    const recentResults = [rank, ...(existing?.recentResults ?? [])].slice(0, RECENT_RESULTS_LIMIT);
    updated[id] = { racesRun, wins, recentResults };
  }

  return updated;
}
