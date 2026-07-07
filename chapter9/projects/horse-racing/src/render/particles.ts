/**
 * 파티클(폭죽·흙먼지) 생성·갱신·그리기 순수 함수(T14). 생성은 주입 rng로 결정적이고,
 * 갱신은 dt만으로 결정되는 순수 물리로 rng를 소비하지 않는다.
 * 그리기는 T11~T13과 동일하게 주입 `RenderContext`(mock ctx) 위 순수 함수다.
 */
import type { RaceState } from "../sim/types";
import {
  DUST_PARTICLE_BASE_RADIUS,
  DUST_PARTICLE_COLOR,
  DUST_PARTICLE_LIFESPAN,
  DUST_SPAWN_RATE,
  FIREWORK_GRAVITY,
  FIREWORK_PARTICLE_COLORS,
  FIREWORK_PARTICLE_COUNT,
  FIREWORK_PARTICLE_LIFESPAN,
  FIREWORK_PARTICLE_RADIUS,
  FIREWORK_SPEED_MAX,
  FIREWORK_SPEED_MIN,
} from "./types";
import type { FireworkParticle, RaceLayout, RenderContext } from "./types";

/**
 * 원점(originX, originY)에서 사방으로 퍼지는 파티클 `count`개를 생성한다. 각도·속력을
 * 주입 rng로 결정하므로 같은 rng 시퀀스면 같은 파티클 집합을 반환한다(결정론).
 */
export function createFireworkParticles(
  rng: () => number,
  originX: number,
  originY: number,
  count: number = FIREWORK_PARTICLE_COUNT,
): FireworkParticle[] {
  const particles: FireworkParticle[] = [];
  for (let i = 0; i < count; i += 1) {
    const angle = rng() * Math.PI * 2;
    const speed = FIREWORK_SPEED_MIN + rng() * (FIREWORK_SPEED_MAX - FIREWORK_SPEED_MIN);
    particles.push({
      x: originX,
      y: originY,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      remaining: FIREWORK_PARTICLE_LIFESPAN,
      max: FIREWORK_PARTICLE_LIFESPAN,
    });
  }
  return particles;
}

/**
 * dt만큼 위치를 전진시키고(중력 가속 포함) 잔여 수명을 감소시키며, 수명이 소진된
 * (remaining <= 0) 파티클을 제거한다. rng를 소비하지 않는 순수 갱신이다.
 */
export function updateParticles(particles: FireworkParticle[], dt: number): FireworkParticle[] {
  return particles
    .map((particle) => ({
      ...particle,
      x: particle.x + particle.vx * dt,
      y: particle.y + particle.vy * dt + 0.5 * FIREWORK_GRAVITY * dt * dt,
      vy: particle.vy + FIREWORK_GRAVITY * dt,
      remaining: particle.remaining - dt,
    }))
    .filter((particle) => particle.remaining > 0);
}

/**
 * 완주 상태(`state.finished`)에서만 파티클을 그린다. 미완주 상태·빈 파티클 집합이면
 * ctx 명령을 내지 않고 조기 반환한다. 색은 팔레트 순환, 잔여 수명 비율로 페이드아웃한다.
 */
export function drawFireworkParticles(ctx: RenderContext, particles: FireworkParticle[], state: RaceState): void {
  if (!state.finished || particles.length === 0) return;

  ctx.save();
  particles.forEach((particle, index) => {
    ctx.fillStyle = FIREWORK_PARTICLE_COLORS[index % FIREWORK_PARTICLE_COLORS.length];
    ctx.globalAlpha = Math.max(0, Math.min(1, particle.remaining / particle.max));
    ctx.beginPath();
    ctx.arc(particle.x, particle.y, FIREWORK_PARTICLE_RADIUS, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.globalAlpha = 1;
  ctx.restore();
}

/**
 * 발굽 위치에서 뒤·위로 흩어지는 흙먼지 퍼프를 생성한다. 폭죽과 같은 `FireworkParticle`
 * 구조를 재사용하며, 생성은 주입 rng로 결정적이다.
 */
export function createDustPuff(
  rng: () => number,
  originX: number,
  originY: number,
  count: number = 2,
): FireworkParticle[] {
  const particles: FireworkParticle[] = [];
  for (let i = 0; i < count; i += 1) {
    const lifespan = DUST_PARTICLE_LIFESPAN * (0.7 + rng() * 0.6);
    particles.push({
      x: originX + (rng() - 0.5) * 6,
      y: originY + (rng() - 0.5) * 3,
      vx: -(16 + rng() * 34),
      vy: -(5 + rng() * 16),
      remaining: lifespan,
      max: lifespan,
    });
  }
  return particles;
}

/**
 * 달리는 중인 각 러너의 발밑에서 먼지 퍼프를 확률적으로 생성한다. 프레임 dt에
 * `DUST_SPAWN_RATE`를 곱한 확률로 러너당 최대 1퍼프를 만들어 프레임레이트와 무관하게
 * 초당 기대 퍼프 수를 유지한다.
 */
export function spawnDustForRunners(rng: () => number, layout: RaceLayout, dt: number): FireworkParticle[] {
  const spawnChance = Math.min(1, dt * DUST_SPAWN_RATE);
  const spawned: FireworkParticle[] = [];
  for (const runner of layout.runners) {
    if (rng() >= spawnChance) continue;
    spawned.push(...createDustPuff(rng, runner.x - 11, runner.y + 12));
  }
  return spawned;
}

/** 먼지는 중력 대신 감쇠(공기 저항)로 흩어진다. rng 없는 순수 갱신. */
export function updateDustParticles(particles: FireworkParticle[], dt: number): FireworkParticle[] {
  const drag = Math.max(0, 1 - 2.6 * dt);
  return particles
    .map((particle) => ({
      ...particle,
      x: particle.x + particle.vx * dt,
      y: particle.y + particle.vy * dt,
      vx: particle.vx * drag,
      vy: particle.vy * drag,
      remaining: particle.remaining - dt,
    }))
    .filter((particle) => particle.remaining > 0);
}

/** 흙먼지를 그린다. 수명이 줄수록 커지고 옅어져 퍼지는 느낌을 준다. 빈 집합이면 아무것도 그리지 않는다. */
export function drawDustParticles(ctx: RenderContext, particles: FireworkParticle[]): void {
  if (particles.length === 0) return;

  ctx.save();
  ctx.fillStyle = DUST_PARTICLE_COLOR;
  particles.forEach((particle) => {
    const lifeRatio = Math.max(0, Math.min(1, particle.remaining / particle.max));
    ctx.globalAlpha = lifeRatio * 0.45;
    ctx.beginPath();
    ctx.arc(particle.x, particle.y, DUST_PARTICLE_BASE_RADIUS + (1 - lifeRatio) * 3.2, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.globalAlpha = 1;
  ctx.restore();
}
