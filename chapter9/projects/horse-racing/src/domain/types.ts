export interface Stats {
  speed: number;
  stamina: number;
  burst: number;
  luck: number;
}

export const STAT_KEYS: (keyof Stats)[] = ["speed", "stamina", "burst", "luck"];

export type ConditionLevel = "최하" | "부진" | "보통" | "호조" | "최상";

export interface SkillDefinition {
  id: string;
  name: string;
  description: string;
}

export interface HorseProfile {
  id: string;
  number: number;
  name: string;
  color: string;
  personality: string;
  baseStats: Stats;
  skill: SkillDefinition;
}

export interface RaceRecord {
  racesRun: number;
  wins: number;
  /** 최근 순위, 가장 최근 결과가 배열 맨 앞 */
  recentResults: number[];
}

export interface HorseRaceEntry {
  horse: HorseProfile;
  currentStats: Stats;
  condition: ConditionLevel;
  winProbability: number;
  odds: number;
  record: RaceRecord;
}

export type GamePhase =
  | "lobby"
  | "countdown"
  | "racing"
  | "finish"
  | "settlement";
