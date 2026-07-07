import { describe, expect, it } from "vitest";
import {
  createDustPuff,
  createFireworkParticles,
  drawDustParticles,
  drawFireworkParticles,
  spawnDustForRunners,
  updateDustParticles,
  updateParticles,
} from "./particles";
import { createMockRenderContext as createMockCtx } from "./testing";
import { DUST_PARTICLE_LIFESPAN, FIREWORK_PARTICLE_LIFESPAN } from "./types";
import type { RaceLayout } from "./types";
import type { RaceState, RunnerState } from "../sim/types";
import { createSeededRng } from "../sim/rng";

function makeRunner(id: string, position: number): RunnerState {
  return {
    id,
    stats: { speed: 70, stamina: 70, burst: 70, luck: 50 },
    position,
    burstPhase: 0,
    skillId: "",
    skillActivated: false,
    skillActivatedAt: null,
  };
}

function makeState(finished: boolean): RaceState {
  return { runners: [makeRunner("horse-1", 1000)], elapsedTime: 20, finished };
}

describe("createFireworkParticles", () => {
  it("같은 시드 rng로 생성한 두 파티클 집합이 동일하다(결정론)", () => {
    const first = createFireworkParticles(createSeededRng(42), 100, 50, 8);
    const second = createFireworkParticles(createSeededRng(42), 100, 50, 8);
    expect(second).toEqual(first);
  });

  it("모든 파티클이 원점 위치·요청한 개수·초기 수명(max=remaining)을 갖는다", () => {
    const particles = createFireworkParticles(createSeededRng(1), 200, 80, 12);
    expect(particles).toHaveLength(12);
    for (const particle of particles) {
      expect(particle.x).toBe(200);
      expect(particle.y).toBe(80);
      expect(particle.remaining).toBe(FIREWORK_PARTICLE_LIFESPAN);
      expect(particle.max).toBe(FIREWORK_PARTICLE_LIFESPAN);
    }
  });

  it("다른 시드는 다른 속도 벡터를 낸다", () => {
    const a = createFireworkParticles(createSeededRng(1), 0, 0, 4);
    const b = createFireworkParticles(createSeededRng(2), 0, 0, 4);
    expect(a).not.toEqual(b);
  });
});

describe("updateParticles", () => {
  it("한 스텝 dt 갱신 후 위치가 속도에 따라 전진하고 수명이 감소한다", () => {
    const particles = [{ x: 0, y: 0, vx: 10, vy: 0, remaining: 1, max: 1 }];
    const [updated] = updateParticles(particles, 0.1);

    expect(updated.x).toBeCloseTo(1, 5);
    expect(updated.remaining).toBeCloseTo(0.9, 5);
  });

  it("여러 스텝 후 수명이 소진된 파티클이 집합에서 제거된다", () => {
    let particles = [{ x: 0, y: 0, vx: 5, vy: 0, remaining: 0.3, max: 0.3 }];

    particles = updateParticles(particles, 0.2);
    expect(particles).toHaveLength(1);

    particles = updateParticles(particles, 0.2);
    expect(particles).toHaveLength(0);
  });

  it("rng 없이 dt만으로 결정되는 순수 갱신이다(같은 입력은 같은 결과)", () => {
    const base = [{ x: 10, y: 10, vx: 20, vy: -5, remaining: 1, max: 1 }];
    const first = updateParticles(base, 0.05);
    const second = updateParticles(base, 0.05);
    expect(second).toEqual(first);
  });
});

describe("drawFireworkParticles", () => {
  it("완주 상태에서 파티클 좌표로 그리기 명령이 호출된다", () => {
    const ctx = createMockCtx();
    const particles = createFireworkParticles(createSeededRng(1), 300, 120, 3);

    drawFireworkParticles(ctx, particles, makeState(true));

    expect(ctx.arc).toHaveBeenCalledTimes(3);
    expect(ctx.save).toHaveBeenCalled();
    expect(ctx.restore).toHaveBeenCalled();
  });

  it("미완주 상태에서는 파티클이 있어도 그리기 명령이 호출되지 않는다", () => {
    const ctx = createMockCtx();
    const particles = createFireworkParticles(createSeededRng(1), 300, 120, 3);

    drawFireworkParticles(ctx, particles, makeState(false));

    expect(ctx.arc).not.toHaveBeenCalled();
    expect(ctx.save).not.toHaveBeenCalled();
  });

  it("빈 파티클 집합이면 완주 상태여도 그리기 명령이 호출되지 않는다", () => {
    const ctx = createMockCtx();

    drawFireworkParticles(ctx, [], makeState(true));

    expect(ctx.arc).not.toHaveBeenCalled();
  });
});

describe("흙먼지 파티클", () => {
  const LAYOUT: RaceLayout = {
    runners: [
      { id: "a", x: 300, y: 120 },
      { id: "b", x: 260, y: 160 },
    ],
    leaderboard: [
      { id: "a", rank: 1 },
      { id: "b", rank: 2 },
    ],
  };

  it("createDustPuff: 같은 시드 rng로 만든 두 퍼프가 동일하다(결정론)", () => {
    const first = createDustPuff(createSeededRng(7), 100, 50, 3);
    const second = createDustPuff(createSeededRng(7), 100, 50, 3);
    expect(second).toEqual(first);
    expect(first).toHaveLength(3);
    for (const particle of first) {
      expect(particle.vx).toBeLessThan(0); // 달리는 방향 반대(뒤)로 흩어진다.
      expect(particle.remaining).toBeLessThanOrEqual(DUST_PARTICLE_LIFESPAN * 1.3);
    }
  });

  it("spawnDustForRunners: dt가 클수록 생성 확률이 올라가고, rng가 확률 이상이면 생성하지 않는다", () => {
    const always = spawnDustForRunners(() => 0, LAYOUT, 1);
    expect(always.length).toBeGreaterThan(0);

    const never = spawnDustForRunners(() => 0.999, LAYOUT, 0.016);
    expect(never).toHaveLength(0);
  });

  it("updateDustParticles: 감쇠로 속도가 줄고 수명이 소진되면 제거된다", () => {
    const base = [{ x: 0, y: 0, vx: -40, vy: -10, remaining: 0.2, max: 0.5 }];
    const [updated] = updateDustParticles(base, 0.1);
    expect(Math.abs(updated.vx)).toBeLessThan(40);
    expect(updated.remaining).toBeCloseTo(0.1, 5);

    expect(updateDustParticles([updated], 0.2)).toHaveLength(0);
  });

  it("drawDustParticles: 파티클 수만큼 원을 그리고, 빈 집합이면 그리지 않는다", () => {
    const ctx = createMockCtx();
    drawDustParticles(ctx, createDustPuff(createSeededRng(1), 10, 10, 4));
    expect(ctx.arc).toHaveBeenCalledTimes(4);

    const emptyCtx = createMockCtx();
    drawDustParticles(emptyCtx, []);
    expect(emptyCtx.arc).not.toHaveBeenCalled();
  });
});
