/**
 * T20b: 베팅 확정→경주 생성→정산·실황 emit 오케스트레이션(useGameController)이 소비하는
 * 순수 헬퍼. store·loop 부수효과는 없으며 `src/domain`·`src/sim`·`src/ui` 타입과 rng만
 * 의존한다. 정산 계산·회차 변동·순위 산출은 재구현하지 않고 기존 함수를 소비한다.
 */
import { SKILL_CATALOG } from "../domain/horses";
import type { HorseProfile, HorseRaceEntry } from "../domain/types";
import type { SettlementInput } from "../domain/settlement";
import { isPhotoFinish, isSlowMotionTriggered } from "../sim/finish";
import type { RaceParticipant, RaceState, RankedRunner } from "../sim/types";
import type { CommentaryEvent } from "./commentary";

const FALLBACK_HORSE_NAME = "정체불명의 말";
const FALLBACK_SKILL_NAME = "신비한 기술";

function nameForHorse(horses: HorseProfile[], id: string | undefined): string {
  return horses.find((horse) => horse.id === id)?.name ?? FALLBACK_HORSE_NAME;
}

function nameForSkill(skillId: string | undefined): string {
  return SKILL_CATALOG.find((skill) => skill.id === skillId)?.name ?? FALLBACK_SKILL_NAME;
}

/**
 * 로비 스냅샷(`buildLobbyEntries` 결과)의 `currentStats`·보유 스킬로 경주 참가자를 조립한다.
 * 로비에 표시된 스냅샷과 동일한 스탯으로 경주가 진행되게 한다(로비 표시와 경주 결과의 정합).
 */
export function toRaceParticipants(entries: HorseRaceEntry[]): RaceParticipant[] {
  return entries.map((entry) => ({
    id: entry.horse.id,
    stats: entry.currentStats,
    skillId: entry.horse.skill.id,
  }));
}

/**
 * 베팅 말 id·금액과 완주 순위로 정산 입력을 조립한다. 배당률은 베팅 확정 시점의 로비
 * 스냅샷(`entries`)에서 베팅 말의 `odds`를 그대로 쓴다(정산 시점에 다시 굴리지 않음).
 * 적중 여부는 순위 1위(rank === 1)의 말 id가 베팅 말 id와 같은지로 판정한다.
 */
export function buildSettlementInput(
  entries: HorseRaceEntry[],
  betHorseId: string,
  betAmount: number,
  rankings: RankedRunner[],
): SettlementInput {
  const betEntry = entries.find((entry) => entry.horse.id === betHorseId);
  const winnerId = rankings.find((ranking) => ranking.rank === 1)?.id;
  return {
    betAmount,
    odds: betEntry?.odds ?? 1,
    won: winnerId === betHorseId,
  };
}

export interface RaceFrameSnapshot {
  state: RaceState;
  rankings: RankedRunner[];
}

/**
 * 프레임 간 경주 상태를 비교해 실황 이벤트(PRD 4.6의 여섯 종)를 도출한다. `prev`가 null이면
 * 첫 프레임(출발)으로 본다. 대상이 있는 이벤트(`lead-change`·`skill-activation`·`finish`)는
 * 카탈로그에서 이름을 채우고, 찾지 못하면 폴백 문구를 써 `{horseName}` 등 리터럴이 결과
 * 문구에 남지 않게 한다(T16 이월 메모 해소).
 */
export function deriveRaceEvents(
  horses: HorseProfile[],
  prev: RaceFrameSnapshot | null,
  current: RaceFrameSnapshot,
): CommentaryEvent[] {
  if (prev === null) {
    return [{ type: "start" }];
  }

  const events: CommentaryEvent[] = [];

  const prevLeaderId = prev.rankings.find((ranking) => ranking.rank === 1)?.id;
  const currentLeaderId = current.rankings.find((ranking) => ranking.rank === 1)?.id;
  if (currentLeaderId !== undefined && currentLeaderId !== prevLeaderId) {
    events.push({ type: "lead-change", horseName: nameForHorse(horses, currentLeaderId) });
  }

  for (const runner of current.state.runners) {
    const prevRunner = prev.state.runners.find((candidate) => candidate.id === runner.id);
    if (runner.skillActivated && !prevRunner?.skillActivated) {
      events.push({
        type: "skill-activation",
        horseName: nameForHorse(horses, runner.id),
        skillName: nameForSkill(runner.skillId),
      });
    }
  }

  if (!isSlowMotionTriggered(prev.state) && isSlowMotionTriggered(current.state)) {
    events.push({ type: "final-stretch" });
  }

  if (!prev.state.finished && current.state.finished) {
    if (isPhotoFinish(current.state)) {
      events.push({ type: "close-race" });
    }
    events.push({ type: "finish", horseName: nameForHorse(horses, currentLeaderId) });
  }

  return events;
}
