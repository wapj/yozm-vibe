import {
  TRACK_LENGTH,
  type RaceParticipant,
  type RaceState,
  type RankedRunner,
  type RunnerState,
} from "./types";
import {
  isStaminaImmune,
  shouldActivateSkill,
  skillOthersVelocityMultiplier,
  skillVelocityMultiplier,
} from "./skills";

export { TRACK_LENGTH };

/** speed 스탯 1당 초당 진행 거리(임의 단위). */
const SPEED_SCALE = 0.55;
/** 이 진행률(progress) 이전에는 stamina 영향이 없다. */
const STAMINA_FADE_START = 0.6;
/** stamina가 0에 수렴하는 말이 후반 구간에서 감속되는 최대 비율. */
const MAX_STAMINA_FADE = 0.5;
/** burst 구간 변동의 주기(초). 짧을수록 페이스 변화가 잦아 순위 다툼이 빈번해진다. */
const BURST_PERIOD = 3.2;
/** burst 스탯 100 기준 가속 변동 진폭. 사인파라 평균 속도(기대값)에는 영향이 없고 요동 폭만 커진다. */
const BURST_AMPLITUDE = 0.24;

/**
 * step()에 rng를 명시적으로 주입하지 않았을 때 쓰는 기본값. 항상 1을 반환해
 * (발동 확률은 항상 1 미만이므로) 스킬이 발동하지 않아, rng를 모르는 기존
 * 호출부의 동작을 그대로 보존한다.
 */
const NEVER_ACTIVATE_RNG = () => 1;

/** 진행률이 후반 구간에 진입한 뒤에만 stamina 부족분(100 기준)만큼 속도를 깎는다. */
function staminaFactor(progress: number, stamina: number): number {
  if (progress <= STAMINA_FADE_START) return 1;
  const fadeProgress = (progress - STAMINA_FADE_START) / (1 - STAMINA_FADE_START);
  const deficit = Math.max(0, (100 - stamina) / 100);
  return 1 - fadeProgress * deficit * MAX_STAMINA_FADE;
}

/** 말마다 고정된 위상(burstPhase)과 경과 시간으로 구간별 가속 변동을 만든다. */
function burstFactor(elapsedTime: number, burst: number, phase: number): number {
  return (
    1 +
    (burst / 100) * BURST_AMPLITUDE * Math.sin((2 * Math.PI * elapsedTime) / BURST_PERIOD + phase)
  );
}

function instantVelocity(runner: RunnerState, elapsedTime: number, staminaImmune: boolean): number {
  const progress = runner.position / TRACK_LENGTH;
  const baseVelocity = runner.stats.speed * SPEED_SCALE;
  const stamina = staminaImmune ? 1 : staminaFactor(progress, runner.stats.stamina);
  return baseVelocity * stamina * burstFactor(elapsedTime, runner.stats.burst, runner.burstPhase);
}

/** 각 러너 id -> 바로 앞 말과의 거리(공동 선두 포함 선두는 null)를 계산한다. 슬립스트림 발동 조건에 쓰인다. */
function computeGapsAhead(runners: RunnerState[]): Map<string, number | null> {
  const maxPosition = Math.max(...runners.map((runner) => runner.position));
  const sorted = [...runners].sort((a, b) => b.position - a.position);
  const gaps = new Map<string, number | null>();
  sorted.forEach((runner, index) => {
    gaps.set(
      runner.id,
      runner.position >= maxPosition ? null : sorted[index - 1].position - runner.position,
    );
  });
  return gaps;
}

/**
 * 출전마 목록으로 각 말의 위치 0에서 시작하는 경주 상태를 만든다.
 * burst 위상은 rng로 1회 결정되며, 이후 step은 rng 없이 순수하게 진행되어
 * 프레임레이트 무관성과 결정론을 함께 만족한다.
 */
export function createRaceState(
  participants: RaceParticipant[],
  rng: () => number = Math.random,
): RaceState {
  return {
    runners: participants.map((participant) => ({
      id: participant.id,
      stats: participant.stats,
      position: 0,
      burstPhase: rng() * 2 * Math.PI,
      skillId: participant.skillId ?? "",
      skillActivated: false,
      skillActivatedAt: null,
    })),
    elapsedTime: 0,
    finished: false,
  };
}

/** 이미 발동했다면 기존 발동 시각을, 이번 스텝에 새로 발동했다면 그 시각을, 아니면 null을 반환한다. */
function resolveActivatedAt(runner: RunnerState, newlyActivatedAt: Map<string, number>): number | null {
  if (runner.skillActivated) return runner.skillActivatedAt ?? null;
  return newlyActivatedAt.get(runner.id) ?? null;
}

/**
 * 경과 시간 dt만큼 각 말을 전진시킨 새 상태를 반환한다.
 * 진행은 누적된 elapsedTime 기반 적분으로만 이뤄져 프레임레이트와 무관하게 결정된다.
 * 이미 완주했거나 dt가 0 이하이면 상태를 그대로 반환한다.
 * rng는 스킬 발동 판정에만 쓰이며, 생략 시 스킬이 전혀 발동하지 않는다.
 */
export function step(state: RaceState, dt: number, rng: () => number = NEVER_ACTIVATE_RNG): RaceState {
  if (state.finished || dt <= 0) return state;

  const elapsedTime = state.elapsedTime;
  const rankById = new Map(rankRunners(state.runners).map((runner) => [runner.id, runner.rank]));
  const gapAheadById = computeGapsAhead(state.runners);

  const newlyActivatedAt = new Map<string, number>();
  for (const runner of state.runners) {
    if (runner.skillActivated) continue;
    const activates = shouldActivateSkill({
      skillId: runner.skillId ?? "",
      progress: runner.position / TRACK_LENGTH,
      gapAhead: gapAheadById.get(runner.id) ?? null,
      luck: runner.stats.luck,
      rank: rankById.get(runner.id) ?? state.runners.length,
      totalRunners: state.runners.length,
      dt,
      rng,
    });
    if (activates) newlyActivatedAt.set(runner.id, elapsedTime);
  }

  // 흔들기처럼 발동자 본인이 아닌 다른 러너의 속도에 영향을 주는 스킬의 배수를 먼저 집계한다.
  const othersMultiplierById = new Map<string, number>();
  for (const runner of state.runners) {
    const activatedAt = resolveActivatedAt(runner, newlyActivatedAt);
    if (activatedAt === null) continue;
    const multiplier = skillOthersVelocityMultiplier(runner.skillId ?? "", elapsedTime - activatedAt);
    if (multiplier === 1) continue;
    for (const other of state.runners) {
      if (other.id === runner.id) continue;
      othersMultiplierById.set(other.id, (othersMultiplierById.get(other.id) ?? 1) * multiplier);
    }
  }

  const runners = state.runners.map((runner) => {
    const activatedAt = resolveActivatedAt(runner, newlyActivatedAt);
    const elapsedSinceActivation = activatedAt === null ? null : elapsedTime - activatedAt;
    const selfMultiplier =
      elapsedSinceActivation === null
        ? 1
        : skillVelocityMultiplier(runner.skillId ?? "", elapsedSinceActivation);
    const staminaImmune =
      elapsedSinceActivation !== null && isStaminaImmune(runner.skillId ?? "", elapsedSinceActivation);
    const othersMultiplier = othersMultiplierById.get(runner.id) ?? 1;

    const velocity = instantVelocity(runner, elapsedTime, staminaImmune) * selfMultiplier * othersMultiplier;
    const position = Math.min(TRACK_LENGTH, Math.max(0, runner.position + velocity * dt));

    return {
      ...runner,
      position,
      skillActivated: Boolean(runner.skillActivated) || newlyActivatedAt.has(runner.id),
      skillActivatedAt: activatedAt,
    };
  });

  return {
    runners,
    elapsedTime: elapsedTime + dt,
    finished: runners.some((runner) => runner.position >= TRACK_LENGTH),
  };
}

/** 전진 거리 내림차순으로 순위를 매긴다. 동률은 같은 순위를 공유한다. */
export function rankRunners(runners: RunnerState[]): RankedRunner[] {
  const sorted = [...runners].sort((a, b) => b.position - a.position);
  const ranked: RankedRunner[] = [];
  sorted.forEach((runner, index) => {
    const tiedWithPrevious = index > 0 && sorted[index - 1].position === runner.position;
    const rank = tiedWithPrevious ? ranked[index - 1].rank : index + 1;
    ranked.push({ id: runner.id, position: runner.position, rank });
  });
  return ranked;
}
