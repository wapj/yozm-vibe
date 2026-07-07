import type { Stats } from "../domain/types";

/** 트랙 길이(임의 단위). 위치·진행률(progress) 계산의 기준이 된다. */
export const TRACK_LENGTH = 1000;

/** 경주 상태 초기화 입력. 회차 변동이 적용된 currentStats를 그대로 넘긴다. */
export interface RaceParticipant {
  id: string;
  stats: Stats;
  /** 보유 스킬 id(도메인 SkillDefinition.id). 생략 시 스킬 없이 진행한다. */
  skillId?: string;
}

export interface RunnerState {
  id: string;
  stats: Stats;
  position: number;
  /** 구간별 가속 변동(burst)의 위상. 말마다 초기화 시 1회 결정되어 이후 스텝은 rng 없이 결정론적으로 진행된다. */
  burstPhase: number;
  /** 보유 스킬 id. 생략 시 스킬 없이 진행한다. */
  skillId?: string;
  /** 이번 경주에서 스킬을 이미 발동했는지 여부. 경주당 최대 1회 발동 제한에 쓰인다. */
  skillActivated?: boolean;
  /** 발동 시점의 elapsedTime. 미발동이면 null. M4 이펙트/배너가 소비할 발동 이력이다. */
  skillActivatedAt?: number | null;
}

export interface RaceState {
  runners: RunnerState[];
  elapsedTime: number;
  /** 어느 말이든 TRACK_LENGTH 이상 전진하면 true로 전환된다. */
  finished: boolean;
}

export interface RankedRunner {
  id: string;
  position: number;
  /** 동률은 같은 순위를 공유하고 다음 순위를 건너뛰는 표준 경쟁 순위(1224 방식). */
  rank: number;
}
