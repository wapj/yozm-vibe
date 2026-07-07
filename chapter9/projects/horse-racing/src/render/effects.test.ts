import { describe, expect, it, vi } from "vitest";
import { drawSkillBanner, drawSkillEffects, isSkillEffectActive, renderSkillEffects } from "./effects";
import { createMockRenderContext as createMockCtx } from "./testing";
import { SKILL_EFFECT_DURATION } from "./types";
import type { RaceLayout, SkillActivationInfo } from "./types";

const LAYOUT: RaceLayout = {
  runners: [
    { id: "a", x: 100, y: 50 },
    { id: "b", x: 200, y: 100 },
  ],
  leaderboard: [
    { id: "a", rank: 1 },
    { id: "b", rank: 2 },
  ],
};

describe("isSkillEffectActive", () => {
  it("skillActivated 아니면 false", () => {
    expect(isSkillEffectActive(false, 1, 1.1)).toBe(false);
    expect(isSkillEffectActive(undefined, 1, 1.1)).toBe(false);
  });

  it("skillActivatedAt이 null/undefined이면 false", () => {
    expect(isSkillEffectActive(true, null, 1.1)).toBe(false);
    expect(isSkillEffectActive(true, undefined, 1.1)).toBe(false);
  });

  it("발동 창 시작(경계 포함) 동작을 고정한다", () => {
    expect(isSkillEffectActive(true, 5, 5)).toBe(true);
  });

  it("발동 창 끝(경계 포함) 동작을 고정한다", () => {
    expect(isSkillEffectActive(true, 5, 5 + SKILL_EFFECT_DURATION)).toBe(true);
  });

  it("발동 창을 벗어나면 false", () => {
    expect(isSkillEffectActive(true, 5, 5 + SKILL_EFFECT_DURATION + 0.001)).toBe(false);
  });
});

describe("drawSkillEffects", () => {
  it("발동 창 안의 말 좌표에만 이펙트 그리기 명령이 호출된다", () => {
    const ctx = createMockCtx();
    const runners: SkillActivationInfo[] = [
      { id: "a", skillId: "last-spurt", skillActivated: true, skillActivatedAt: 2 },
      { id: "b", skillId: "slipstream", skillActivated: false, skillActivatedAt: null },
    ];

    drawSkillEffects(ctx, LAYOUT, runners, 2.5);

    expect(ctx.arc).toHaveBeenCalled();
    const arcCalls = (ctx.arc as ReturnType<typeof vi.fn>).mock.calls.map((call) => [call[0], call[1]]);
    for (const [x, y] of arcCalls) {
      expect([x, y]).toEqual([100, 50]);
    }

    const moveToCalls = (ctx.moveTo as ReturnType<typeof vi.fn>).mock.calls.map((call) => [call[0], call[1]]);
    for (const [x, y] of moveToCalls) {
      expect([x, y]).toEqual([100, 50]);
    }
  });

  it("발동 창을 벗어나면 그리기 명령이 호출되지 않는다", () => {
    const ctx = createMockCtx();
    const runners: SkillActivationInfo[] = [
      { id: "a", skillId: "last-spurt", skillActivated: true, skillActivatedAt: 2 },
    ];

    drawSkillEffects(ctx, LAYOUT, runners, 2 + SKILL_EFFECT_DURATION + 1);

    expect(ctx.arc).not.toHaveBeenCalled();
    expect(ctx.moveTo).not.toHaveBeenCalled();
  });

  it("미발동 말은 그리기 명령이 호출되지 않는다", () => {
    const ctx = createMockCtx();
    const runners: SkillActivationInfo[] = [{ id: "a", skillActivated: false, skillActivatedAt: null }];

    drawSkillEffects(ctx, LAYOUT, runners, 1);

    expect(ctx.arc).not.toHaveBeenCalled();
  });
});

describe("drawSkillBanner", () => {
  it("발동 창 안의 말에 대해 도메인 표시명이 fillText로 노출된다", () => {
    const ctx = createMockCtx();
    const runners: SkillActivationInfo[] = [
      { id: "a", skillId: "last-spurt", skillActivated: true, skillActivatedAt: 1 },
      { id: "b", skillId: "slipstream", skillActivated: true, skillActivatedAt: 1 },
    ];

    drawSkillBanner(ctx, LAYOUT, runners, 1.2);

    const texts = (ctx.fillText as ReturnType<typeof vi.fn>).mock.calls.map((call) => call[0] as string);
    expect(texts).toContain("라스트 스퍼트");
    expect(texts).toContain("슬립스트림");
  });

  it("발동 창을 벗어나면 배너가 그려지지 않는다", () => {
    const ctx = createMockCtx();
    const runners: SkillActivationInfo[] = [
      { id: "a", skillId: "last-spurt", skillActivated: true, skillActivatedAt: 1 },
    ];

    drawSkillBanner(ctx, LAYOUT, runners, 1 + SKILL_EFFECT_DURATION + 1);

    expect(ctx.fillText).not.toHaveBeenCalled();
  });
});

describe("방어 분기(T13 흡수, T12 REVIEW 테스트 충실도 메모)", () => {
  it("drawSkillEffects: layout에 없는 러너는 좌표 부재로 예외 없이 건너뛴다(effects.ts:82)", () => {
    const ctx = createMockCtx();
    const runners: SkillActivationInfo[] = [
      { id: "missing", skillId: "last-spurt", skillActivated: true, skillActivatedAt: 0 },
    ];

    expect(() => drawSkillEffects(ctx, LAYOUT, runners, 0.1)).not.toThrow();
    expect(ctx.arc).not.toHaveBeenCalled();
  });

  it("drawSkillBanner: skillId가 없는 러너는 배너 없이 예외 없이 건너뛴다(effects.ts:103)", () => {
    const ctx = createMockCtx();
    const runners: SkillActivationInfo[] = [{ id: "a", skillActivated: true, skillActivatedAt: 0 }];

    expect(() => drawSkillBanner(ctx, LAYOUT, runners, 0.1)).not.toThrow();
    expect(ctx.fillText).not.toHaveBeenCalled();
  });

  it("drawSkillBanner: 도메인 카탈로그에 없는 미지 skillId는 id 그대로 폴백해 노출된다(effects.ts:106)", () => {
    const ctx = createMockCtx();
    const runners: SkillActivationInfo[] = [
      { id: "a", skillId: "unknown-skill", skillActivated: true, skillActivatedAt: 0 },
    ];

    drawSkillBanner(ctx, LAYOUT, runners, 0.1);

    expect(ctx.fillText).toHaveBeenCalledWith("unknown-skill", 100, expect.any(Number));
  });
});

describe("renderSkillEffects", () => {
  it("이펙트와 배너를 함께 그린다", () => {
    const ctx = createMockCtx();
    const runners: SkillActivationInfo[] = [
      { id: "a", skillId: "zone", skillActivated: true, skillActivatedAt: 0 },
    ];

    renderSkillEffects(ctx, LAYOUT, runners, 0.1);

    expect(ctx.arc).toHaveBeenCalled();
    expect(ctx.fillText).toHaveBeenCalledWith("무아지경", 100, expect.any(Number));
  });
});
