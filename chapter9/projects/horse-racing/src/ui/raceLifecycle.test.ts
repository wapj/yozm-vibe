import { describe, expect, it } from "vitest";
import { createHorseCatalog } from "../domain/horses";
import type { HorseRaceEntry } from "../domain/types";
import type { RaceState, RankedRunner, RunnerState } from "../sim/types";
import { buildSettlementInput, deriveRaceEvents, toRaceParticipants, type RaceFrameSnapshot } from "./raceLifecycle";

const HORSES = createHorseCatalog(3);

function buildEntries(): HorseRaceEntry[] {
  return HORSES.map((horse, index) => ({
    horse,
    currentStats: horse.baseStats,
    condition: "보통" as const,
    winProbability: 0.3,
    odds: 2 + index,
    record: { racesRun: 0, wins: 0, recentResults: [] },
  }));
}

function runner(id: string, overrides: Partial<RunnerState> = {}): RunnerState {
  return {
    id,
    stats: { speed: 50, stamina: 50, burst: 50, luck: 50 },
    position: 0,
    burstPhase: 0,
    skillId: HORSES.find((horse) => horse.id === id)?.skill.id ?? "",
    skillActivated: false,
    skillActivatedAt: null,
    ...overrides,
  };
}

function raceState(runners: RunnerState[], overrides: Partial<RaceState> = {}): RaceState {
  return { runners, elapsedTime: 0, finished: false, ...overrides };
}

function rankings(order: string[]): RankedRunner[] {
  return order.map((id, index) => ({ id, position: 1000 - index, rank: index + 1 }));
}

describe("toRaceParticipants", () => {
  it("HorseRaceEntry[]의 currentStats·보유 스킬로 RaceParticipant[]를 조립한다", () => {
    const entries = buildEntries();
    const participants = toRaceParticipants(entries);

    expect(participants).toEqual(
      entries.map((entry) => ({
        id: entry.horse.id,
        stats: entry.currentStats,
        skillId: entry.horse.skill.id,
      })),
    );
  });
});

describe("buildSettlementInput", () => {
  it("적중 시 베팅 말 스냅샷 odds로 won=true를 반환한다", () => {
    const entries = buildEntries();
    const betHorseId = entries[1].horse.id;
    const input = buildSettlementInput(entries, betHorseId, 500, rankings([betHorseId, entries[0].horse.id]));

    expect(input).toEqual({ betAmount: 500, odds: entries[1].odds, won: true });
  });

  it("미적중 시 won=false를 반환한다", () => {
    const entries = buildEntries();
    const betHorseId = entries[1].horse.id;
    const input = buildSettlementInput(
      entries,
      betHorseId,
      500,
      rankings([entries[0].horse.id, betHorseId]),
    );

    expect(input).toEqual({ betAmount: 500, odds: entries[1].odds, won: false });
  });
});

describe("deriveRaceEvents", () => {
  const [a, b] = HORSES.map((horse) => horse.id);

  it("prev가 null이면 출발 이벤트만 반환한다", () => {
    const current: RaceFrameSnapshot = { state: raceState([runner(a), runner(b)]), rankings: rankings([a, b]) };
    expect(deriveRaceEvents(HORSES, null, current)).toEqual([{ type: "start" }]);
  });

  it("선두 id가 프레임 간 바뀌면 lead-change 이벤트를 도출하고 말 이름을 채운다", () => {
    const prev: RaceFrameSnapshot = { state: raceState([runner(a), runner(b)]), rankings: rankings([a, b]) };
    const current: RaceFrameSnapshot = { state: raceState([runner(a), runner(b)]), rankings: rankings([b, a]) };

    const events = deriveRaceEvents(HORSES, prev, current);
    expect(events).toContainEqual({
      type: "lead-change",
      horseName: HORSES.find((horse) => horse.id === b)?.name,
    });
  });

  it("skillActivated가 false→true로 바뀌면 skillActivatedAt이 설정되고 skill-activation 이벤트를 도출한다", () => {
    const prevRunners = [runner(a), runner(b)];
    const currentRunners = [
      { ...runner(a), skillActivated: true, skillActivatedAt: 1.5 },
      runner(b),
    ];
    const prev: RaceFrameSnapshot = { state: raceState(prevRunners), rankings: rankings([a, b]) };
    const current: RaceFrameSnapshot = { state: raceState(currentRunners), rankings: rankings([a, b]) };

    expect(currentRunners[0].skillActivatedAt).toBe(1.5);
    const events = deriveRaceEvents(HORSES, prev, current);
    const horseA = HORSES.find((horse) => horse.id === a)!;
    expect(events).toContainEqual({
      type: "skill-activation",
      horseName: horseA.name,
      skillName: horseA.skill.name,
    });
  });

  it("슬로모션 트리거가 false→true로 바뀌면 final-stretch 이벤트를 도출한다", () => {
    const prev: RaceFrameSnapshot = {
      state: raceState([runner(a, { position: 800 }), runner(b, { position: 700 })]),
      rankings: rankings([a, b]),
    };
    const current: RaceFrameSnapshot = {
      state: raceState([runner(a, { position: 950 }), runner(b, { position: 700 })]),
      rankings: rankings([a, b]),
    };

    expect(deriveRaceEvents(HORSES, prev, current)).toContainEqual({ type: "final-stretch" });
  });

  it("완주 전환 시 finish 이벤트를 도출하고, 접전이면 close-race도 함께 도출한다", () => {
    const prev: RaceFrameSnapshot = {
      state: raceState([runner(a, { position: 995 }), runner(b, { position: 990 })]),
      rankings: rankings([a, b]),
    };
    const current: RaceFrameSnapshot = {
      state: raceState([runner(a, { position: 1000 }), runner(b, { position: 995 })], { finished: true }),
      rankings: rankings([a, b]),
    };

    const events = deriveRaceEvents(HORSES, prev, current);
    expect(events).toContainEqual({ type: "close-race" });
    expect(events).toContainEqual({
      type: "finish",
      horseName: HORSES.find((horse) => horse.id === a)?.name,
    });
  });

  it("카탈로그에 없는 id는 폴백 이름으로 채운다", () => {
    const prev: RaceFrameSnapshot = {
      state: raceState([runner("unknown-horse"), runner(b)]),
      rankings: rankings([b, "unknown-horse"]),
    };
    const current: RaceFrameSnapshot = {
      state: raceState([runner("unknown-horse"), runner(b)]),
      rankings: rankings(["unknown-horse", b]),
    };

    const events = deriveRaceEvents(HORSES, prev, current);
    const leadChange = events.find((event) => event.type === "lead-change");
    expect(leadChange?.horseName).toBe("정체불명의 말");
  });

  it("완주하지 않고 선두 교체·스킬 발동이 없으면 빈 배열을 반환한다", () => {
    const prev: RaceFrameSnapshot = { state: raceState([runner(a), runner(b)]), rankings: rankings([a, b]) };
    const current: RaceFrameSnapshot = {
      state: raceState([runner(a, { position: 10 }), runner(b, { position: 5 })]),
      rankings: rankings([a, b]),
    };

    expect(deriveRaceEvents(HORSES, prev, current)).toEqual([]);
  });
});
