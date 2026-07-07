import { describe, expect, it } from "vitest";
import { createRaceState, rankRunners, step, TRACK_LENGTH } from "./engine";
import type { RaceParticipant, RaceState } from "./types";

const participants: RaceParticipant[] = [
  { id: "horse-1", stats: { speed: 80, stamina: 70, burst: 60, luck: 50 } },
  { id: "horse-2", stats: { speed: 65, stamina: 85, burst: 75, luck: 40 } },
  { id: "horse-3", stats: { speed: 72, stamina: 55, burst: 50, luck: 60 } },
];

function runFixedSteps(state: RaceState, dt: number, steps: number): RaceState {
  let current = state;
  for (let i = 0; i < steps; i++) {
    current = step(current, dt);
  }
  return current;
}

describe("createRaceState", () => {
  it("모든 말의 위치 0, elapsedTime 0, finished false로 초기화한다", () => {
    const state = createRaceState(participants, () => 0.5);

    expect(state.elapsedTime).toBe(0);
    expect(state.finished).toBe(false);
    expect(state.runners).toHaveLength(participants.length);
    for (const runner of state.runners) {
      expect(runner.position).toBe(0);
    }
  });
});

describe("프레임레이트 독립성", () => {
  it("같은 초기 상태·같은 RNG 시퀀스에서 큰 스텝 1회와 작은 스텝 N회 누적 결과가 허용 오차 내로 일치한다", () => {
    const T = 1;
    const N = 100;
    const tolerance = TRACK_LENGTH * 0.01;

    const bigStepState = runFixedSteps(createRaceState(participants, () => 0.5), T, 1);
    const smallStepState = runFixedSteps(createRaceState(participants, () => 0.5), T / N, N);

    bigStepState.runners.forEach((runner, index) => {
      const other = smallStepState.runners[index];
      expect(Math.abs(runner.position - other.position)).toBeLessThanOrEqual(tolerance);
    });
  });
});

describe("결정론", () => {
  it("동일 초기 상태·동일 RNG로 두 번 시뮬레이션하면 매 스텝 위치가 완전히 동일하다", () => {
    const rng = () => 0.5;
    let stateA = createRaceState(participants, rng);
    let stateB = createRaceState(participants, rng);

    for (let i = 0; i < 50; i++) {
      stateA = step(stateA, 0.1);
      stateB = step(stateB, 0.1);
      expect(stateA.runners).toEqual(stateB.runners);
    }
  });
});

describe("rankRunners", () => {
  it("전진 거리 내림차순으로 순위를 매긴다", () => {
    const ranked = rankRunners([
      { id: "a", stats: participants[0].stats, position: 300, burstPhase: 0 },
      { id: "b", stats: participants[1].stats, position: 500, burstPhase: 0 },
      { id: "c", stats: participants[2].stats, position: 100, burstPhase: 0 },
    ]);

    expect(ranked.map((r) => r.id)).toEqual(["b", "a", "c"]);
    expect(ranked.map((r) => r.rank)).toEqual([1, 2, 3]);
  });

  it("동률인 말은 같은 순위를 공유하고 다음 순위를 건너뛴다", () => {
    const ranked = rankRunners([
      { id: "a", stats: participants[0].stats, position: 500, burstPhase: 0 },
      { id: "b", stats: participants[1].stats, position: 500, burstPhase: 0 },
      { id: "c", stats: participants[2].stats, position: 200, burstPhase: 0 },
    ]);

    expect(ranked.map((r) => r.rank)).toEqual([1, 1, 3]);
  });
});

describe("완주 판정", () => {
  it("어느 말도 트랙 길이에 도달하기 전에는 finished가 false다", () => {
    let state = createRaceState(participants, () => 0.5);
    state = runFixedSteps(state, 0.5, 5);

    expect(state.finished).toBe(false);
  });

  it("어느 말이든 트랙 길이 이상 전진하면 finished가 true로 전환된다", () => {
    const fastParticipants: RaceParticipant[] = [
      { id: "horse-1", stats: { speed: 200, stamina: 100, burst: 0, luck: 50 } },
    ];
    let state = createRaceState(fastParticipants, () => 0.5);
    state = runFixedSteps(state, 1, 20);

    expect(state.finished).toBe(true);
    expect(state.runners[0].position).toBeGreaterThanOrEqual(TRACK_LENGTH);
  });
});

describe("후반 감속 (stamina)", () => {
  it("stamina가 낮은 말은 경주 후반 구간에서 순간 속도가 초반 대비 감소한다", () => {
    const lowStaminaStats = { speed: 70, stamina: 10, burst: 0, luck: 50 };

    const earlyState: RaceState = {
      runners: [{ id: "horse-1", stats: lowStaminaStats, position: 0, burstPhase: 0 }],
      elapsedTime: 0,
      finished: false,
    };
    const lateState: RaceState = {
      runners: [
        { id: "horse-1", stats: lowStaminaStats, position: TRACK_LENGTH * 0.9, burstPhase: 0 },
      ],
      elapsedTime: 0,
      finished: false,
    };

    const dt = 0.01;
    const earlyVelocity = (step(earlyState, dt).runners[0].position - earlyState.runners[0].position) / dt;
    const lateVelocity = (step(lateState, dt).runners[0].position - lateState.runners[0].position) / dt;

    expect(lateVelocity).toBeLessThan(earlyVelocity);
  });
});
