/**
 * 피니시 연출 순수 함수(T13): 슬로모션 dt 배율 산출과 포토 피니시/우승 결과 배너 그리기.
 * 판정은 sim `finish.ts`(`isSlowMotionTriggered`·`isPhotoFinish`)를 그대로 소비하고
 * 진행률·접전 계산을 재구현하지 않는다. 좌표·순위는 T10 `computeRaceLayout` 결과와
 * `RunnerMeta`에서만 가져온다.
 */
import { isPhotoFinish, isSlowMotionTriggered } from "../sim/finish";
import type { RaceState } from "../sim/types";
import { SLOW_MOTION_TIME_SCALE, WINNER_SPOTLIGHT_COLOR, WINNER_SPOTLIGHT_RADIUS } from "./types";
import type { Dimensions, RaceLayout, RenderContext, RunnerMeta } from "./types";

const PHOTO_FINISH_TEXT = "포토 피니시!";
const FINISH_BANNER_COLOR = "#ffffff";
const FINISH_BANNER_FONT = "bold 30px sans-serif";
const BANNER_PANEL_COLOR = "#12151c";
const BANNER_ACCENT_COLOR = "#ffd60a";
const BANNER_PANEL_WIDTH = 400;
const BANNER_PANEL_HEIGHT = 74;

/**
 * 선두 진행률이 threshold 이상(`isSlowMotionTriggered`)이면 `SLOW_MOTION_TIME_SCALE`,
 * 아니면 1.0을 반환한다. 완주(`finished=true`) 이후에도 같은 판정을 그대로 위임하므로,
 * 완주 시점의 선두 위치가 트랙 길이에 도달해 진행률이 threshold를 넘는 한 슬로모션이
 * 자동으로 유지된다(완주 직후 해제하지 않음: T8 REVIEW 메모 1 정책 결정 — 트리거
 * 조건의 자연스러운 귀결을 따르며 별도 해제 로직을 두지 않는다).
 */
export function computeSlowMotionTimeScale(state: RaceState, threshold?: number): number {
  return isSlowMotionTriggered(state, threshold) ? SLOW_MOTION_TIME_SCALE : 1.0;
}

/**
 * 완주 상태에서 결과 배너를 그린다. 접전(`isPhotoFinish`)이면 포토 피니시 문구를,
 * 아니면 1위 러너의 번호·이름을 병기한 우승 배너를 그린다(PRD 4.5). 미완주 상태에서는
 * 아무것도 그리지 않는다. 문구 fillText는 배너당 1회로 유지한다(T20a 테스트 계약).
 */
export function drawFinishBanner(
  ctx: RenderContext,
  dimensions: Dimensions,
  layout: RaceLayout,
  runnersMeta: RunnerMeta[],
  state: RaceState,
): void {
  if (!state.finished) return;

  ctx.save();

  const centerX = dimensions.width / 2;
  const centerY = dimensions.height / 2;

  // 화면을 살짝 어둡게 눌러 배너에 시선을 모은다.
  ctx.globalAlpha = 0.38;
  ctx.fillStyle = "#05070c";
  ctx.fillRect(0, 0, dimensions.width, dimensions.height);

  // 결과 패널: 어두운 판 + 금색 상하 라인.
  ctx.globalAlpha = 0.92;
  ctx.fillStyle = BANNER_PANEL_COLOR;
  ctx.fillRect(centerX - BANNER_PANEL_WIDTH / 2, centerY - BANNER_PANEL_HEIGHT / 2, BANNER_PANEL_WIDTH, BANNER_PANEL_HEIGHT);
  ctx.globalAlpha = 1;
  ctx.fillStyle = BANNER_ACCENT_COLOR;
  ctx.fillRect(centerX - BANNER_PANEL_WIDTH / 2, centerY - BANNER_PANEL_HEIGHT / 2 - 3, BANNER_PANEL_WIDTH, 3);
  ctx.fillRect(centerX - BANNER_PANEL_WIDTH / 2, centerY + BANNER_PANEL_HEIGHT / 2, BANNER_PANEL_WIDTH, 3);

  ctx.font = FINISH_BANNER_FONT;
  ctx.fillStyle = FINISH_BANNER_COLOR;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  if (isPhotoFinish(state)) {
    ctx.fillText(PHOTO_FINISH_TEXT, centerX, centerY);
  } else {
    const winner = layout.leaderboard.find((entry) => entry.rank === 1);
    const meta = winner ? runnersMeta.find((candidate) => candidate.id === winner.id) : undefined;
    const label = meta ? `우승! ${meta.number}번 ${meta.name}` : "우승!";
    ctx.fillText(label, centerX, centerY);
  }

  ctx.restore();
}

/**
 * 완주 상태에서 우승마(1위)의 layout 좌표를 강조하는 스포트라이트를 그린다. 좌표는
 * `layout.runners`/`layout.leaderboard`에서만 가져오며 순위·좌표를 재구현하지 않는다.
 * 미완주 상태(우승마 미확정)에서는 아무것도 그리지 않는다. 동심원 3겹으로 부드러운
 * 글로우를 만들며 기준 반경(`WINNER_SPOTLIGHT_RADIUS`) 원을 반드시 포함한다.
 */
export function drawWinnerSpotlight(ctx: RenderContext, layout: RaceLayout, state: RaceState): void {
  if (!state.finished) return;

  const winner = layout.leaderboard.find((entry) => entry.rank === 1);
  const position = winner ? layout.runners.find((runner) => runner.id === winner.id) : undefined;
  if (!position) return;

  ctx.save();
  ctx.fillStyle = WINNER_SPOTLIGHT_COLOR;
  for (const [radiusScale, alpha] of [
    [1.7, 0.35],
    [1.3, 0.55],
    [1, 1],
  ]) {
    ctx.globalAlpha = alpha;
    ctx.beginPath();
    ctx.arc(position.x, position.y, WINNER_SPOTLIGHT_RADIUS * radiusScale, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
  ctx.restore();
}
