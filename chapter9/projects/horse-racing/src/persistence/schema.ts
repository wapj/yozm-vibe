import type { RaceRecord } from "../domain/types";

export const STORAGE_KEY = "horse-racing:save:v1";
export const SAVE_SCHEMA_VERSION = 1;

export const DEFAULT_BALANCE = 10000;
export const MIN_HORSE_COUNT = 4;
export const MAX_HORSE_COUNT = 8;
export const DEFAULT_HORSE_COUNT = 5;

export interface GameSettings {
  horseCount: number;
  muted: boolean;
}

/** localStorage에 저장되는 전체 상태. records는 말 id를 키로 하는 전적 맵이다. */
export interface SavedState {
  version: number;
  balance: number;
  bankruptcyCount: number;
  records: Record<string, RaceRecord>;
  settings: GameSettings;
}

export function createDefaultSettings(): GameSettings {
  return { horseCount: DEFAULT_HORSE_COUNT, muted: false };
}

export function createDefaultState(): SavedState {
  return {
    version: SAVE_SCHEMA_VERSION,
    balance: DEFAULT_BALANCE,
    bankruptcyCount: 0,
    records: {},
    settings: createDefaultSettings(),
  };
}

function isRaceRecord(value: unknown): value is RaceRecord {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.racesRun === "number" &&
    typeof record.wins === "number" &&
    Array.isArray(record.recentResults) &&
    record.recentResults.every((entry) => typeof entry === "number")
  );
}

function isGameSettings(value: unknown): value is GameSettings {
  if (typeof value !== "object" || value === null) return false;
  const settings = value as Record<string, unknown>;
  return (
    typeof settings.horseCount === "number" &&
    settings.horseCount >= MIN_HORSE_COUNT &&
    settings.horseCount <= MAX_HORSE_COUNT &&
    typeof settings.muted === "boolean"
  );
}

/** 파싱된 임의의 값을 검증해 SavedState로 좁힌다. 스키마와 불일치하면 null을 반환한다. */
export function validateSavedState(value: unknown): SavedState | null {
  if (typeof value !== "object" || value === null) return null;
  const candidate = value as Record<string, unknown>;

  if (candidate.version !== SAVE_SCHEMA_VERSION) return null;
  if (typeof candidate.balance !== "number" || Number.isNaN(candidate.balance)) return null;
  if (typeof candidate.bankruptcyCount !== "number" || Number.isNaN(candidate.bankruptcyCount)) {
    return null;
  }
  if (typeof candidate.records !== "object" || candidate.records === null) return null;

  const records = candidate.records as Record<string, unknown>;
  for (const key of Object.keys(records)) {
    if (!isRaceRecord(records[key])) return null;
  }
  if (!isGameSettings(candidate.settings)) return null;

  return {
    version: candidate.version,
    balance: candidate.balance,
    bankruptcyCount: candidate.bankruptcyCount,
    records: records as Record<string, RaceRecord>,
    settings: candidate.settings,
  };
}
