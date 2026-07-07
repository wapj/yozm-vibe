import { afterEach, describe, expect, it, vi } from "vitest";
import type { HorseProfile } from "../domain/types";
import { TRACK_LENGTH } from "../sim/types";
import type { RaceState, RunnerState } from "../sim/types";
import { createMockRenderContext as createMockCtx } from "./testing";
import type { FireworkParticle } from "./types";

vi.mock("./finishFx", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./finishFx")>();
  return {
    ...actual,
    drawFinishBanner: vi.fn(),
    drawWinnerSpotlight: vi.fn(),
  };
});

vi.mock("./particles", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./particles")>();
  return {
    ...actual,
    drawFireworkParticles: vi.fn(),
  };
});

const { drawFinishBanner, drawWinnerSpotlight } = await import("./finishFx");
const { drawFireworkParticles } = await import("./particles");
const { renderScene, deriveRunnersMeta, deriveSkillRunners, computeSceneLayout, computeCameraShake } =
  await import("./renderScene");

const DIMENSIONS = { width: 800, height: 300 };

const CATALOG: HorseProfile[] = [
  {
    id: "horse-1",
    number: 1,
    name: "번개질주",
    color: "#e63946",
    personality: "저돌적",
    baseStats: { speed: 88, stamina: 60, burst: 70, luck: 45 },
    skill: { id: "start-dash", name: "스타트 대시", description: "" },
  },
  {
    id: "horse-2",
    number: 2,
    name: "은빛바람",
    color: "#457b9d",
    personality: "냉정함",
    baseStats: { speed: 75, stamina: 82, burst: 55, luck: 50 },
    skill: { id: "last-spurt", name: "라스트 스퍼트", description: "" },
  },
];

const RUNNERS_META = deriveRunnersMeta(CATALOG);

afterEach(() => {
  vi.clearAllMocks();
});

function makeRunner(id: string, position: number, overrides: Partial<RunnerState> = {}): RunnerState {
  return {
    id,
    stats: { speed: 70, stamina: 70, burst: 70, luck: 50 },
    position,
    burstPhase: 0,
    skillId: "",
    skillActivated: false,
    skillActivatedAt: null,
    ...overrides,
  };
}

function makeState(positions: number[], finished: boolean, elapsedTime = 3): RaceState {
  return {
    runners: positions.map((position, index) => makeRunner(`horse-${index + 1}`, position)),
    elapsedTime,
    finished,
  };
}

describe("deriveRunnersMeta", () => {
  it("카탈로그에서 번호·이름·색만 추린다", () => {
    expect(RUNNERS_META).toEqual([
      { id: "horse-1", number: 1, name: "번개질주", color: "#e63946" },
      { id: "horse-2", number: 2, name: "은빛바람", color: "#457b9d" },
    ]);
  });
});

describe("deriveSkillRunners", () => {
  it("러너 상태에서 발동 이력만 추린다", () => {
    const state = makeState([100, 50], false);
    state.runners[0].skillId = "start-dash";
    state.runners[0].skillActivated = true;
    state.runners[0].skillActivatedAt = 1.5;

    expect(deriveSkillRunners(state)).toEqual([
      { id: "horse-1", skillId: "start-dash", skillActivated: true, skillActivatedAt: 1.5 },
      { id: "horse-2", skillId: "", skillActivated: false, skillActivatedAt: null },
    ]);
  });
});

describe("renderScene", () => {
  it("미완주 프레임: 트랙·말·순위표는 그려지고 피니시 배너·스포트라이트·폭죽은 그려지지 않는다", () => {
    const ctx = createMockCtx();
    const state = makeState([TRACK_LENGTH * 0.5, TRACK_LENGTH * 0.3], false);

    renderScene(ctx, DIMENSIONS, state, RUNNERS_META);

    expect(ctx.fillRect).toHaveBeenCalled(); // drawTrack

    // drawRunners: 각 러너가 씬 레이아웃 좌표로 이동되어 그려진다.
    const layout = computeSceneLayout(state, DIMENSIONS);
    const translateCalls = (ctx.translate as ReturnType<typeof vi.fn>).mock.calls;
    for (const runner of layout.runners) {
      expect(translateCalls).toContainEqual([runner.x, runner.y]);
    }

    // drawLeaderboard: 번호·이름 병기 라벨이 노출된다.
    const texts = (ctx.fillText as ReturnType<typeof vi.fn>).mock.calls.map((call) => call[0] as string);
    expect(texts).toContain("1번 번개질주");
    expect(texts).toContain("2번 은빛바람");

    expect(drawFinishBanner).not.toHaveBeenCalled();
    expect(drawWinnerSpotlight).not.toHaveBeenCalled();
    expect(drawFireworkParticles).not.toHaveBeenCalled();
  });

  it("완주 프레임: 피니시 배너·스포트라이트·폭죽이 함께 호출되고, 전달된 layout이 computeSceneLayout 결과와 일치한다", () => {
    const ctx = createMockCtx();
    const state = makeState([TRACK_LENGTH, TRACK_LENGTH - 500], true);
    const particles: FireworkParticle[] = [
      { x: 10, y: 20, vx: 1, vy: -1, remaining: 1, max: 1.2 },
    ];

    renderScene(ctx, DIMENSIONS, state, RUNNERS_META, particles);

    const expectedLayout = computeSceneLayout(state, DIMENSIONS);

    expect(drawFinishBanner).toHaveBeenCalledWith(ctx, DIMENSIONS, expectedLayout, RUNNERS_META, state);
    expect(drawWinnerSpotlight).toHaveBeenCalledWith(ctx, expectedLayout, state);
    expect(drawFireworkParticles).toHaveBeenCalledWith(ctx, particles, state);
  });

  it("완주 프레임에서도 호출 순서는 트랙/말/순위표 → 피니시 배너 → 스포트라이트 → 폭죽이다", () => {
    const ctx = createMockCtx();
    const state = makeState([TRACK_LENGTH, TRACK_LENGTH - 500], true);

    renderScene(ctx, DIMENSIONS, state, RUNNERS_META);

    const bannerOrder = (drawFinishBanner as ReturnType<typeof vi.fn>).mock.invocationCallOrder[0];
    const spotlightOrder = (drawWinnerSpotlight as ReturnType<typeof vi.fn>).mock.invocationCallOrder[0];
    const fireworkOrder = (drawFireworkParticles as ReturnType<typeof vi.fn>).mock.invocationCallOrder[0];

    expect(bannerOrder).toBeLessThan(spotlightOrder);
    expect(spotlightOrder).toBeLessThan(fireworkOrder);
  });

  it("빈 파티클 목록(기본값)으로도 예외 없이 완주 프레임을 그린다", () => {
    const ctx = createMockCtx();
    const state = makeState([TRACK_LENGTH, TRACK_LENGTH - 500], true);

    expect(() => renderScene(ctx, DIMENSIONS, state, RUNNERS_META)).not.toThrow();
    expect(drawFireworkParticles).toHaveBeenCalledWith(ctx, [], state);
  });
});

describe("접전 연출(카메라 셰이크·레터박스)", () => {
  it("종반(슬로모션 트리거) 미완주 구간에서만 카메라 셰이크가 발생한다", () => {
    const finale = makeState([TRACK_LENGTH * 0.95, TRACK_LENGTH * 0.93], false);
    const shake = computeCameraShake(finale);
    expect(shake.x !== 0 || shake.y !== 0).toBe(true);

    const midRace = makeState([TRACK_LENGTH * 0.5, TRACK_LENGTH * 0.3], false);
    expect(computeCameraShake(midRace)).toEqual({ x: 0, y: 0 });

    const finished = makeState([TRACK_LENGTH, TRACK_LENGTH - 5], true);
    expect(computeCameraShake(finished)).toEqual({ x: 0, y: 0 });
  });

  it("1·2위가 초접전이면 '대접전!' 문구가, 아니면 '결승선 스퍼트!' 문구가 그려진다", () => {
    const neckAndNeck = createMockCtx();
    renderScene(neckAndNeck, DIMENSIONS, makeState([TRACK_LENGTH * 0.95, TRACK_LENGTH * 0.94], false), RUNNERS_META);
    const closeTexts = (neckAndNeck.fillText as ReturnType<typeof vi.fn>).mock.calls.map((call) => call[0] as string);
    expect(closeTexts).toContain("대접전!");

    const spurt = createMockCtx();
    renderScene(spurt, DIMENSIONS, makeState([TRACK_LENGTH * 0.95, TRACK_LENGTH * 0.5], false), RUNNERS_META);
    const spurtTexts = (spurt.fillText as ReturnType<typeof vi.fn>).mock.calls.map((call) => call[0] as string);
    expect(spurtTexts).toContain("결승선 스퍼트!");
  });

  it("평상시(중반) 프레임에는 접전 문구가 그려지지 않는다", () => {
    const ctx = createMockCtx();
    renderScene(ctx, DIMENSIONS, makeState([TRACK_LENGTH * 0.5, TRACK_LENGTH * 0.3], false), RUNNERS_META);
    const texts = (ctx.fillText as ReturnType<typeof vi.fn>).mock.calls.map((call) => call[0] as string);
    expect(texts).not.toContain("대접전!");
    expect(texts).not.toContain("결승선 스퍼트!");
  });
});
