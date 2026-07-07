/**
 * 스킬 발동 이펙트(확산 오라·회전 스파크)와 스킬명 배너를 그리는 순수 함수(T12).
 * 발동 이력(`skillActivated`·`skillActivatedAt`)과 현재 `elapsedTime`을 인자로만
 * 소비하며 발동 판정을 재구현하지 않고, 러너 좌표는 T10 `computeRaceLayout` 결과
 * (`layout.runners`)에서만 가져온다. 스킬 표시명은 도메인 `SKILL_CATALOG`을 그대로
 * 소비하며 문자열을 하드코딩하지 않는다.
 */
import { SKILL_CATALOG } from "../domain/horses";
import { HORSE_BODY_RADIUS, SKILL_EFFECT_DURATION } from "./types";
import type { RaceLayout, RenderContext, SkillActivationInfo } from "./types";

const SKILL_NAME_BY_ID = new Map(SKILL_CATALOG.map((skill) => [skill.id, skill.name]));

/** 부동소수점 오차(예: 5 + 1.2 - 5 = 1.2000000000000002)로 경계값 판정이 어긋나지 않게 하는 허용 오차. */
const BOUNDARY_EPSILON = 1e-9;

const EFFECT_COLOR = "#ffd60a";
const EFFECT_RING_COUNT = 3;
const EFFECT_BASE_RADIUS = HORSE_BODY_RADIUS * 1.5;
const EFFECT_RING_GROWTH = HORSE_BODY_RADIUS * 0.8;
/** 발동 창 진행에 따라 링이 추가로 퍼지는 최대 반경. */
const EFFECT_RING_SPREAD = HORSE_BODY_RADIUS * 1.6;
const EFFECT_LINE_COUNT = 8;
const EFFECT_LINE_LENGTH = HORSE_BODY_RADIUS * 2.8;

const BANNER_TEXT_COLOR = "#ffd60a";
const BANNER_FONT = "bold 13px sans-serif";
const BANNER_OFFSET_Y = HORSE_BODY_RADIUS * 3.4;
/** 발동 창 동안 배너가 위로 떠오르는 거리(px). */
const BANNER_RISE_DISTANCE = 9;
/** 배너 배경 알약의 글자당 폭 근사(px). measureText 없이 배경 폭을 정한다. */
const BANNER_CHAR_WIDTH = 13.5;

/**
 * `skillActivated`이고 `elapsedTime`이 발동 시점부터 `SKILL_EFFECT_DURATION`
 * 이내(양 끝 포함)이면 true. 미발동(`skillActivated` 아님/`skillActivatedAt=null`)
 * 이거나 창을 벗어나면 false.
 */
export function isSkillEffectActive(
  skillActivated: boolean | undefined,
  skillActivatedAt: number | null | undefined,
  elapsedTime: number,
): boolean {
  if (!skillActivated || skillActivatedAt == null) return false;
  const sinceActivation = elapsedTime - skillActivatedAt;
  return sinceActivation >= -BOUNDARY_EPSILON && sinceActivation <= SKILL_EFFECT_DURATION + BOUNDARY_EPSILON;
}

/** 발동 창 내 진행률(0~1). 창 밖 값은 0~1로 클램프한다. */
function effectProgress(skillActivatedAt: number | null | undefined, elapsedTime: number): number {
  if (skillActivatedAt == null) return 0;
  return Math.max(0, Math.min(1, (elapsedTime - skillActivatedAt) / SKILL_EFFECT_DURATION));
}

function layoutPositionById(layout: RaceLayout): Map<string, { x: number; y: number }> {
  return new Map(layout.runners.map((runner) => [runner.id, { x: runner.x, y: runner.y }]));
}

/** 확산하며 옅어지는 링과 회전하는 스파크 라인. 모든 arc·moveTo는 러너 좌표 (x, y)를 중심으로 한다. */
function drawAura(ctx: RenderContext, x: number, y: number, progress: number): void {
  ctx.save();
  ctx.strokeStyle = EFFECT_COLOR;
  ctx.lineWidth = 2;
  ctx.globalAlpha = Math.max(0, 1 - progress * 0.85);

  for (let ring = 0; ring < EFFECT_RING_COUNT; ring += 1) {
    const radius = EFFECT_BASE_RADIUS + ring * EFFECT_RING_GROWTH + progress * EFFECT_RING_SPREAD;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.stroke();
  }

  const sparkLength = EFFECT_LINE_LENGTH * (0.55 + 0.45 * Math.sin(progress * Math.PI));
  for (let line = 0; line < EFFECT_LINE_COUNT; line += 1) {
    const angle = ((Math.PI * 2) / EFFECT_LINE_COUNT) * line + progress * 2.4;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + Math.cos(angle) * sparkLength, y + Math.sin(angle) * sparkLength);
    ctx.stroke();
  }

  ctx.globalAlpha = 1;
  ctx.restore();
}

/** 발동 창 안의 각 러너 좌표(`layout.runners`)에 오라·스파크 이펙트를 그린다. */
export function drawSkillEffects(
  ctx: RenderContext,
  layout: RaceLayout,
  runners: SkillActivationInfo[],
  elapsedTime: number,
): void {
  const positionById = layoutPositionById(layout);

  runners.forEach((runner) => {
    if (!isSkillEffectActive(runner.skillActivated, runner.skillActivatedAt, elapsedTime)) return;
    const position = positionById.get(runner.id);
    if (!position) return;
    drawAura(ctx, position.x, position.y, effectProgress(runner.skillActivatedAt, elapsedTime));
  });
}

/** 발동 창 안의 각 러너 위에 도메인 표시명(예: 라스트 스퍼트)을 떠오르는 배너로 그린다. */
export function drawSkillBanner(
  ctx: RenderContext,
  layout: RaceLayout,
  runners: SkillActivationInfo[],
  elapsedTime: number,
): void {
  const positionById = layoutPositionById(layout);

  ctx.save();
  ctx.font = BANNER_FONT;
  ctx.textAlign = "center";
  ctx.textBaseline = "bottom";

  runners.forEach((runner) => {
    if (!isSkillEffectActive(runner.skillActivated, runner.skillActivatedAt, elapsedTime)) return;
    if (!runner.skillId) return;
    const position = positionById.get(runner.id);
    if (!position) return;

    const displayName = SKILL_NAME_BY_ID.get(runner.skillId) ?? runner.skillId;
    const progress = effectProgress(runner.skillActivatedAt, elapsedTime);
    const textY = position.y - BANNER_OFFSET_Y - progress * BANNER_RISE_DISTANCE;
    const pillWidth = displayName.length * BANNER_CHAR_WIDTH + 14;

    ctx.globalAlpha = Math.max(0, 1 - progress * 0.75) * 0.7;
    ctx.fillStyle = "#0c0f14";
    ctx.fillRect(position.x - pillWidth / 2, textY - 16, pillWidth, 19);

    ctx.globalAlpha = Math.max(0, 1 - progress * 0.75);
    ctx.fillStyle = BANNER_TEXT_COLOR;
    ctx.fillText(displayName, position.x, textY);
  });

  ctx.globalAlpha = 1;
  ctx.restore();
}

/** 스킬 이펙트와 배너를 함께 그리는 진입점. `renderRace`가 이 순서로 호출한다. */
export function renderSkillEffects(
  ctx: RenderContext,
  layout: RaceLayout,
  runners: SkillActivationInfo[],
  elapsedTime: number,
): void {
  drawSkillEffects(ctx, layout, runners, elapsedTime);
  drawSkillBanner(ctx, layout, runners, elapsedTime);
}
