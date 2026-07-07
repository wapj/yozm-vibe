import type { HorseRaceEntry } from "../domain/types";
import { hasWinStreakBadge } from "./lobbyEntries";

export interface HorseCardProps {
  entry: HorseRaceEntry;
}

const RECENT_RESULTS_DISPLAY_COUNT = 5;

/** PRD 4.1·4.3·4.7: 출전마 한 마리의 스탯·컨디션·배당률·전적·연승 배지를 표시한다. */
export function HorseCard({ entry }: HorseCardProps) {
  const { horse, condition, odds, record } = entry;
  const recentResults = record.recentResults.slice(0, RECENT_RESULTS_DISPLAY_COUNT);
  const recentResultsText = recentResults.length > 0 ? recentResults.join("-") : "-";
  const winRate = record.racesRun > 0 ? (record.wins / record.racesRun) * 100 : 0;
  const showWinStreakBadge = hasWinStreakBadge(record.recentResults);

  return (
    <article className="card horse-card" aria-label={`${horse.number}번 ${horse.name}`}>
      <header className="horse-card__header">
        <span>{`${horse.number}번`}</span>
        <span>{horse.name}</span>
        {showWinStreakBadge && (
          <span className="horse-card__badge" aria-label="연승 배지">
            연승
          </span>
        )}
      </header>
      <p>{`컨디션: ${condition}`}</p>
      <p>{`배당률: ${odds.toFixed(1)}배`}</p>
      <p>{`전적: ${record.racesRun}전 ${record.wins}승 (승률 ${winRate.toFixed(1)}%)`}</p>
      <p>{`최근 ${RECENT_RESULTS_DISPLAY_COUNT}경기: ${recentResultsText}`}</p>
    </article>
  );
}
