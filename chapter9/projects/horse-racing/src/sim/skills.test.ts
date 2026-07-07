import { describe, expect, it } from "vitest";
import { createRaceState, step, TRACK_LENGTH } from "./engine";
import {
  activationProbability,
  isSkillEligible,
  isStaminaImmune,
  skillOthersVelocityMultiplier,
  skillVelocityMultiplier,
} from "./skills";
import type { RaceParticipant, RaceState } from "./types";
import type { Stats } from "../domain/types";

const baseStats: Stats = { speed: 70, stamina: 80, burst: 40, luck: 50 };

describe("activationProbability", () => {
  it("동일 luck·동일 조건에서 하위 순위 말의 발동 확률이 상위 순위 말보다 높다", () => {
    const topRank = activationProbability(50, 1, 5, 1);
    const bottomRank = activationProbability(50, 5, 5, 1);

    expect(bottomRank).toBeGreaterThan(topRank);
  });

  it("같은 순위에서 luck이 높을수록 발동 확률이 높다", () => {
    const lowLuck = activationProbability(10, 3, 5, 1);
    const highLuck = activationProbability(90, 3, 5, 1);

    expect(highLuck).toBeGreaterThan(lowLuck);
  });

  it("출전마가 1마리뿐이어도(순위 분모 0) NaN 없이 확률을 계산한다", () => {
    const probability = activationProbability(50, 1, 1, 1);

    expect(Number.isNaN(probability)).toBe(false);
    expect(probability).toBeGreaterThan(0);
    expect(probability).toBeLessThan(1);
  });
});

describe("isSkillEligible: 스킬별 발동 가능 구간", () => {
  it("start-dash는 초반 구간에서만 발동 가능하다", () => {
    expect(isSkillEligible("start-dash", 0.05, null)).toBe(true);
    expect(isSkillEligible("start-dash", 0.5, null)).toBe(false);
  });

  it("last-spurt는 종반 구간에서만 발동 가능하다", () => {
    expect(isSkillEligible("last-spurt", 0.5, null)).toBe(false);
    expect(isSkillEligible("last-spurt", 0.8, null)).toBe(true);
  });

  it("슬립스트림은 앞 말과의 간격이 충분히 가까울 때만 발동 가능하다", () => {
    expect(isSkillEligible("slipstream", 0.5, 10)).toBe(true);
    expect(isSkillEligible("slipstream", 0.5, 100)).toBe(false);
    expect(isSkillEligible("slipstream", 0.5, null)).toBe(false);
  });

  it("정의되지 않은 스킬 id는 항상 발동 불가다", () => {
    expect(isSkillEligible("unknown-skill", 0.5, 0)).toBe(false);
  });
});

describe("스킬 효과: 대표 유형별 순간 속도 변화", () => {
  it("start-dash는 발동 중 본인 속도를 높이고, 지속시간 이후에는 원래대로 돌아간다", () => {
    expect(skillVelocityMultiplier("start-dash", 0)).toBeGreaterThan(1);
    expect(skillVelocityMultiplier("start-dash", 10)).toBe(1);
  });

  it("last-spurt는 발동 중 본인 속도를 크게 높인다", () => {
    expect(skillVelocityMultiplier("last-spurt", 1)).toBeGreaterThan(1);
  });

  it("흔들기는 본인 속도에는 영향이 없고, 다른 말의 속도만 낮춘다", () => {
    expect(skillVelocityMultiplier("shake-off", 1)).toBe(1);
    expect(skillOthersVelocityMultiplier("shake-off", 1)).toBeLessThan(1);
  });

  it("무아지경은 발동 중 stamina 소모(후반 감속)를 면제한다", () => {
    expect(isStaminaImmune("zone", 1)).toBe(true);
    expect(isStaminaImmune("zone", 10)).toBe(false);
  });
});

describe("경주당 1회 발동 제한", () => {
  it("한 번 발동한 말은 이후 스텝에서 발동 조건이 다시 충족돼도 재발동하지 않는다", () => {
    const alwaysActivateRng = () => 0;
    const participants: RaceParticipant[] = [{ id: "horse-1", stats: baseStats, skillId: "shake-off" }];

    let state = createRaceState(participants, () => 0.5);
    state = {
      ...state,
      runners: [{ ...state.runners[0], position: TRACK_LENGTH * 0.3 }],
    };

    state = step(state, 1, alwaysActivateRng);
    expect(state.runners[0].skillActivated).toBe(true);
    const firstActivatedAt = state.runners[0].skillActivatedAt;

    for (let i = 0; i < 5; i++) {
      state = step(state, 0.5, alwaysActivateRng);
    }

    expect(state.runners[0].skillActivated).toBe(true);
    expect(state.runners[0].skillActivatedAt).toBe(firstActivatedAt);
  });
});

describe("엔진 통합: 스킬 발동이 실제 위치 증가분에 반영된다", () => {
  it("start-dash가 발동하면 미발동 대비 더 멀리 전진한다", () => {
    const participants: RaceParticipant[] = [{ id: "horse-1", stats: baseStats, skillId: "start-dash" }];

    const activatedState = step(createRaceState(participants, () => 0), 0.5, () => 0);
    const notActivatedState = step(createRaceState(participants, () => 0), 0.5, () => 1);

    expect(activatedState.runners[0].skillActivated).toBe(true);
    expect(notActivatedState.runners[0].skillActivated).toBe(false);
    expect(activatedState.runners[0].position).toBeGreaterThan(notActivatedState.runners[0].position);
  });

  it("흔들기가 발동하면 다른 말은 미발동 상황 대비 덜 전진한다", () => {
    const participants: RaceParticipant[] = [
      { id: "shaker", stats: baseStats, skillId: "shake-off" },
      { id: "victim", stats: baseStats, skillId: "last-spurt" },
    ];

    // shake-off는 진행률 0.2~0.9 구간에서만 발동 가능하므로, 두 말을 그 구간으로 옮겨 둔다.
    function atMidRace(): RaceState {
      const state = createRaceState(participants, () => 0);
      return {
        ...state,
        runners: state.runners.map((runner) => ({ ...runner, position: TRACK_LENGTH * 0.3 })),
      };
    }

    const activatedState = step(atMidRace(), 0.5, () => 0);
    const notActivatedState = step(atMidRace(), 0.5, () => 1);

    const victimActivated = activatedState.runners.find((runner) => runner.id === "victim")!;
    const victimNotActivated = notActivatedState.runners.find((runner) => runner.id === "victim")!;

    expect(victimActivated.position).toBeLessThan(victimNotActivated.position);
  });
});

describe("burst 효과 직접 검증", () => {
  it("burst가 큰 말의 순간 속도 변동 진폭이 burst=0인 말보다 크다", () => {
    const highBurstStats: Stats = { speed: 70, stamina: 100, burst: 100, luck: 50 };
    const noBurstStats: Stats = { speed: 70, stamina: 100, burst: 0, luck: 50 };

    function velocityAt(stats: Stats, elapsedTime: number): number {
      const dt = 0.001;
      const state: RaceState = {
        runners: [
          {
            id: "x",
            stats,
            position: TRACK_LENGTH * 0.1,
            burstPhase: 0,
          },
        ],
        elapsedTime,
        finished: false,
      };
      const next = step(state, dt);
      return (next.runners[0].position - state.runners[0].position) / dt;
    }

    const sampleTimes = Array.from({ length: 20 }, (_, i) => (i / 20) * 4);
    const highAmplitudeSamples = sampleTimes.map((t) => velocityAt(highBurstStats, t));
    const noAmplitudeSamples = sampleTimes.map((t) => velocityAt(noBurstStats, t));

    const amplitude = (values: number[]) => Math.max(...values) - Math.min(...values);

    expect(amplitude(highAmplitudeSamples)).toBeGreaterThan(amplitude(noAmplitudeSamples));
  });
});

describe("결정론", () => {
  function mulberry32(seed: number): () => number {
    let a = seed;
    return () => {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  it("동일 RNG 시퀀스에서 스킬 발동 여부·시각·효과가 완전히 재현된다", () => {
    const participants: RaceParticipant[] = [
      { id: "horse-1", stats: { ...baseStats, luck: 90 }, skillId: "last-spurt" },
      { id: "horse-2", stats: { ...baseStats, luck: 60 }, skillId: "shake-off" },
    ];

    function run(): RaceState {
      let state = createRaceState(participants, mulberry32(42));
      const stepRng = mulberry32(7);
      for (let i = 0; i < 40; i++) {
        state = step(state, 0.2, stepRng);
      }
      return state;
    }

    expect(run()).toEqual(run());
  });
});
