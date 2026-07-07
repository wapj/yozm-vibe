/** 5종 스킬(PRD 4.2)의 효과·발동 조건·발동 확률을 정의하는 순수 모듈. */

export const SKILL_IDS = ["last-spurt", "slipstream", "start-dash", "shake-off", "zone"] as const;
export type SkillId = (typeof SKILL_IDS)[number];

interface SkillConfig {
  /** 발동 후 효과가 지속되는 시간(초). */
  duration: number;
  /** 현재 진행률·앞 말과의 간격으로 발동 가능 여부를 결정한다. */
  eligible(progress: number, gapAhead: number | null): boolean;
  /** 발동 중 본인 순간 속도에 곱하는 배수. */
  selfMultiplier: number;
  /** 발동 중 다른 모든 말의 순간 속도에 곱하는 배수(흔들기 전용). 없으면 영향 없음. */
  othersMultiplier?: number;
  /** 발동 중 stamina 소모(후반 감속)를 무시하는지 여부(무아지경 전용). */
  staminaImmune?: boolean;
}

const SKILL_CONFIG: { [key: string]: SkillConfig | undefined } = {
  "last-spurt": {
    duration: 4,
    eligible: (progress) => progress >= 0.75,
    selfMultiplier: 2.4,
  },
  slipstream: {
    duration: 6,
    eligible: (_progress, gapAhead) => gapAhead !== null && gapAhead <= 40,
    selfMultiplier: 1.6,
  },
  "start-dash": {
    duration: 2,
    eligible: (progress) => progress <= 0.15,
    selfMultiplier: 2.2,
  },
  "shake-off": {
    duration: 3,
    eligible: (progress) => progress >= 0.2 && progress <= 0.9,
    selfMultiplier: 1,
    othersMultiplier: 0.55,
  },
  zone: {
    duration: 6,
    eligible: (progress) => progress >= 0.5,
    selfMultiplier: 1.4,
    staminaImmune: true,
  },
};

/** 발동 확률(초당 해저드율)의 기본값. luck·순위 보정이 없어도 존재하는 최소 확률. */
const BASE_ACTIVATION_HAZARD = 0.01;
/** luck 1당 초당 해저드율 증가분. */
const LUCK_HAZARD_WEIGHT = 0.0003;
/** 최하위(상대 순위 1.0) 보정 시 초당 해저드율 증가분. 하위권일수록 역전 가능성을 높인다(PRD 4.2). */
const RANK_HAZARD_WEIGHT = 0.5;

/**
 * luck·현재 순위 기반 초당 해저드율을 dt 동안의 발동 확률로 변환한다.
 * 순위는 1(선두)~totalRunners(최하위)이며, 상대 순위가 클수록(하위권일수록) 확률이 높아진다.
 */
export function activationProbability(
  luck: number,
  rank: number,
  totalRunners: number,
  dt: number,
): number {
  const relativeRank = totalRunners > 1 ? (rank - 1) / (totalRunners - 1) : 0;
  const hazard = BASE_ACTIVATION_HAZARD + luck * LUCK_HAZARD_WEIGHT + relativeRank * RANK_HAZARD_WEIGHT;
  return 1 - Math.exp(-hazard * dt);
}

/** 스킬 종류별 발동 가능 구간(진행률·앞 말과의 간격) 조건을 만족하는지 확인한다. */
export function isSkillEligible(skillId: string, progress: number, gapAhead: number | null): boolean {
  const config = SKILL_CONFIG[skillId];
  return config ? config.eligible(progress, gapAhead) : false;
}

/**
 * 이번 스텝에 스킬이 발동해야 하는지 판정한다. 순수 함수이며, 무작위성은
 * 주입된 rng를 통해서만 소비되어 동일 rng 시퀀스에서 결과가 재현된다.
 * 경주당 1회 발동 제한은 이미 발동한 러너를 호출 전에 걸러내는 쪽(엔진)의 책임이다.
 */
export function shouldActivateSkill(params: {
  skillId: string;
  progress: number;
  gapAhead: number | null;
  luck: number;
  rank: number;
  totalRunners: number;
  dt: number;
  rng: () => number;
}): boolean {
  if (!isSkillEligible(params.skillId, params.progress, params.gapAhead)) return false;
  const probability = activationProbability(params.luck, params.rank, params.totalRunners, params.dt);
  return params.rng() < probability;
}

/** 발동 중(0 <= elapsedSinceActivation < duration)이면 본인 속도 배수를, 아니면 1을 반환한다. */
export function skillVelocityMultiplier(skillId: string, elapsedSinceActivation: number): number {
  const config = SKILL_CONFIG[skillId];
  if (!config) return 1;
  if (elapsedSinceActivation < 0 || elapsedSinceActivation >= config.duration) return 1;
  return config.selfMultiplier;
}

/** 발동 중이면 다른 말들에 적용할 속도 배수를(흔들기 전용) 반환하고, 그 외에는 1(영향 없음)을 반환한다. */
export function skillOthersVelocityMultiplier(skillId: string, elapsedSinceActivation: number): number {
  const config = SKILL_CONFIG[skillId];
  if (!config?.othersMultiplier) return 1;
  if (elapsedSinceActivation < 0 || elapsedSinceActivation >= config.duration) return 1;
  return config.othersMultiplier;
}

/** 발동 중 stamina 소모(후반 감속)를 무시해야 하는지 반환한다(무아지경 전용). */
export function isStaminaImmune(skillId: string, elapsedSinceActivation: number): boolean {
  const config = SKILL_CONFIG[skillId];
  if (!config?.staminaImmune) return false;
  return elapsedSinceActivation >= 0 && elapsedSinceActivation < config.duration;
}
