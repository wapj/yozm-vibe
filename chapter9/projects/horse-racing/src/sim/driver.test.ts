import { describe, expect, it } from "vitest";
import {
  advanceWithAccumulator,
  createAccumulator,
  FIXED_SUBSTEP,
  runRaceToCompletion,
} from "./driver";
import { createRaceState, rankRunners, step, TRACK_LENGTH } from "./engine";
import { isPhotoFinish, isSlowMotionTriggered } from "./finish";
import { createSeededRng } from "./rng";
import { createHorseCatalog } from "../domain/horses";
import { applyStatVariance } from "../domain/stats";
import type { RaceParticipant, RaceState, RankedRunner } from "./types";

function catalogParticipants(count: number): RaceParticipant[] {
  return createHorseCatalog(count).map((horse) => ({
    id: horse.id,
    stats: horse.baseStats,
    skillId: horse.skill.id,
  }));
}

/** state를 fixedStep 단위로 최대 seconds초(또는 완주까지) 진행시킨다. */
function driveFor(state: RaceState, rng: () => number, seconds: number, fixedStep = FIXED_SUBSTEP): RaceState {
  let current = state;
  let elapsed = 0;
  while (elapsed < seconds && !current.finished) {
    current = step(current, fixedStep, rng);
    elapsed += fixedStep;
  }
  return current;
}

describe("프레임레이트 독립성 (전체 완주 구간)", () => {
  it("스킬 발동이 포함된 전체 경주에서 큰 raw dt와 작은 raw dt로 진행한 결과가 허용 오차 내로 일치한다", () => {
    function driveWithRawDt(rawDt: number): RaceState {
      const rng = createSeededRng(2024);
      let state = createRaceState(catalogParticipants(5), rng);
      let accumulator = createAccumulator();
      let safety = 0;
      while (!state.finished && safety < 200_000) {
        const advanced = advanceWithAccumulator(state, accumulator, rawDt, rng);
        state = advanced.state;
        accumulator = advanced.accumulator;
        safety++;
      }
      return state;
    }

    const lowFpsState = driveWithRawDt(1); // 1fps급 저사양 프레임(1초짜리 큰 raw dt)
    const highFpsState = driveWithRawDt(1 / 240); // 240fps급 고사양 프레임(잘게 쪼갠 raw dt)

    const tolerance = TRACK_LENGTH * 0.01;
    for (const runner of lowFpsState.runners) {
      const other = highFpsState.runners.find((candidate) => candidate.id === runner.id)!;
      expect(Math.abs(runner.position - other.position)).toBeLessThanOrEqual(tolerance);
    }
    expect(Math.abs(lowFpsState.elapsedTime - highFpsState.elapsedTime)).toBeLessThanOrEqual(FIXED_SUBSTEP * 2);
    expect(rankRunners(lowFpsState.runners).map((r) => r.id)).toEqual(
      rankRunners(highFpsState.runners).map((r) => r.id),
    );
  });
});

describe("완주 시간 범위", () => {
  it("기본 카탈로그 스탯(회차 변동 미적용)으로 완주하면 PRD 4.5의 15~30초 범위에 든다", () => {
    const participants = catalogParticipants(5);
    const result = runRaceToCompletion(participants, createSeededRng(1));

    expect(result.finalState.finished).toBe(true);
    expect(result.finishTime).toBeGreaterThanOrEqual(15);
    expect(result.finishTime).toBeLessThanOrEqual(30);
  });

  it("여러 시드에서도 완주 시간이 범위를 벗어나지 않는다", () => {
    for (let seed = 1; seed <= 20; seed++) {
      const participants = catalogParticipants(5);
      const result = runRaceToCompletion(participants, createSeededRng(seed * 31 + 7));

      expect(result.finishTime).toBeGreaterThanOrEqual(15);
      expect(result.finishTime).toBeLessThanOrEqual(30);
    }
  });
});

describe("역전 우승 빈도", () => {
  it("출발 초반 하위권 말이 우승하는 회차 비율이 PRD 9번 목표(대략 10~20%) 근방에 든다", () => {
    const RACE_COUNT = 200;
    const SNAPSHOT_TIME = 2;
    let reversalCount = 0;

    for (let seed = 1; seed <= RACE_COUNT; seed++) {
      const rng = createSeededRng(seed * 104_729 + 17);
      const participants = createHorseCatalog(5).map((horse) => ({
        id: horse.id,
        stats: applyStatVariance(horse.baseStats, rng),
        skillId: horse.skill.id,
      }));

      let state = createRaceState(participants, rng);
      let earlyRanks: RankedRunner[] | null = null;
      while (!state.finished) {
        state = step(state, FIXED_SUBSTEP, rng);
        if (earlyRanks === null && state.elapsedTime >= SNAPSHOT_TIME) {
          earlyRanks = rankRunners(state.runners);
        }
      }

      const total = participants.length;
      const bottomHalfIds = new Set(
        (earlyRanks ?? []).filter((ranked) => ranked.rank > total / 2).map((ranked) => ranked.id),
      );
      const winner = rankRunners(state.runners).find((ranked) => ranked.rank === 1)!;
      if (bottomHalfIds.has(winner.id)) reversalCount++;
    }

    const reversalRatio = reversalCount / RACE_COUNT;
    expect(reversalRatio).toBeGreaterThanOrEqual(0.05);
    expect(reversalRatio).toBeLessThanOrEqual(0.35);
  });
});

describe("zone·slipstream 엔진 위치 반영 (통합)", () => {
  it("zone이 실제 rng로 발동하면 미발동 대비 위치가 증가한다", () => {
    const stats = { speed: 65, stamina: 55, burst: 40, luck: 95 };
    let verified = false;

    for (let seed = 1; seed <= 300 && !verified; seed++) {
      const withRng = createSeededRng(seed);
      const withState = driveFor(
        createRaceState([{ id: "x", stats, skillId: "zone" }], withRng),
        withRng,
        25,
      );
      if (!withState.runners[0].skillActivated) continue;

      const withoutRng = createSeededRng(seed);
      const withoutState = driveFor(
        createRaceState([{ id: "x", stats, skillId: "" }], withoutRng),
        withoutRng,
        25,
      );

      expect(withState.runners[0].position).toBeGreaterThan(withoutState.runners[0].position);
      verified = true;
    }

    expect(verified).toBe(true);
  });

  it("slipstream이 실제 rng로 발동하면 미발동 대비 위치가 증가한다", () => {
    const leaderStats = { speed: 80, stamina: 70, burst: 50, luck: 50 };
    const chaserStats = { speed: 70, stamina: 70, burst: 50, luck: 95 };

    function buildState(chaserSkillId: string): RaceState {
      return {
        runners: [
          {
            id: "leader",
            stats: leaderStats,
            position: 200,
            burstPhase: 0,
            skillId: "",
            skillActivated: false,
            skillActivatedAt: null,
          },
          {
            id: "chaser",
            stats: chaserStats,
            position: 170,
            burstPhase: 0,
            skillId: chaserSkillId,
            skillActivated: false,
            skillActivatedAt: null,
          },
        ],
        elapsedTime: 0,
        finished: false,
      };
    }

    let verified = false;
    for (let seed = 1; seed <= 500 && !verified; seed++) {
      const withRng = createSeededRng(seed);
      const withState = driveFor(buildState("slipstream"), withRng, 8);
      const chaserWith = withState.runners.find((runner) => runner.id === "chaser")!;
      if (!chaserWith.skillActivated) continue;

      const withoutRng = createSeededRng(seed);
      const withoutState = driveFor(buildState(""), withoutRng, 8);
      const chaserWithout = withoutState.runners.find((runner) => runner.id === "chaser")!;

      expect(chaserWith.position).toBeGreaterThan(chaserWithout.position);
      verified = true;
    }

    expect(verified).toBe(true);
  });
});

describe("maxTime 미완주 분기 (T9 REVIEW 메모 2)", () => {
  it("극단적으로 낮은 speed 입력이면 완주하지 못하고 finished=false로 maxTime에서 안전 종료한다", () => {
    const participants: RaceParticipant[] = [
      { id: "slow", stats: { speed: 0.001, stamina: 50, burst: 0, luck: 0 } },
    ];

    const result = runRaceToCompletion(participants, createSeededRng(1), { maxTime: 5 });

    expect(result.finalState.finished).toBe(false);
    expect(result.finishTime).toBeGreaterThanOrEqual(5);
    expect(result.finishTime).toBeLessThan(5 + FIXED_SUBSTEP * 2);
  });
});

describe("러너 수 하한 유지 (통합)", () => {
  it("실제 카탈로그(4~8마리)를 구동기에 주입해도 러너 수가 항상 2 이상이라 피니시 판정이 안전하다", () => {
    for (let count = 4; count <= 8; count++) {
      const participants = catalogParticipants(count);
      const result = runRaceToCompletion(participants, createSeededRng(count * 97 + 3));

      expect(result.finalState.runners.length).toBeGreaterThanOrEqual(2);
      expect(() => isSlowMotionTriggered(result.finalState)).not.toThrow();
      expect(() => isPhotoFinish(result.finalState)).not.toThrow();
      expect(isPhotoFinish(result.finalState)).toEqual(expect.any(Boolean));
    }
  });
});
