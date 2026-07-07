/**
 * 한 프레임 전체를 그리는 순수 조합 함수(T20a). `createRenderLoop`의 `onFrame`이
 * 소비하며, 좌표는 `computeSceneLayout`(T10 `computeRaceLayout`에 트랙 지오메트리
 * 여백을 주입)으로 얻고 그리기는 기존 M4 함수(`renderRace`·`finishFx`·`particles`)를
 * 그대로 소비한다. 좌표·순위·발동 이력·파티클 물리를 재구현하지 않으며,
 * `src/store`·`src/sim` 엔진을 직접 import하지 않고 도메인 타입(`HorseProfile`)과
 * sim 도메인 타입(`RaceState`)·판정 함수(`isSlowMotionTriggered`)만 의존한다.
 */
import type { HorseProfile } from "../domain/types";
import { isSlowMotionTriggered } from "../sim/finish";
import { TRACK_LENGTH } from "../sim/types";
import type { RaceState } from "../sim/types";
import { computeRaceLayout } from "./layout";
import { drawFinishBanner, drawWinnerSpotlight } from "./finishFx";
import { drawDustParticles, drawFireworkParticles } from "./particles";
import { computeTrackGeometry, renderRace } from "./renderer";
import { CAMERA_SHAKE_AMPLITUDE, CINEMATIC_BAR_RATIO } from "./types";
import type { Dimensions, FireworkParticle, RaceLayout, RenderContext, RunnerMeta, SkillActivationInfo } from "./types";

/** 1·2위 위치 차가 트랙 길이의 이 비율 이하면 종반 연출 문구를 '대접전'으로 승격한다. */
const NECK_AND_NECK_GAP_RATIO = 0.04;

/** 말 카탈로그(`HorseProfile[]`)에서 렌더러가 필요로 하는 번호·이름·색만 추린다. */
export function deriveRunnersMeta(catalog: HorseProfile[]): RunnerMeta[] {
  return catalog.map((horse) => ({
    id: horse.id,
    number: horse.number,
    name: horse.name,
    color: horse.color,
  }));
}

/** 시뮬레이션 러너 상태에서 스킬 이펙트/배너가 필요로 하는 발동 이력만 추린다. */
export function deriveSkillRunners(state: RaceState): SkillActivationInfo[] {
  return state.runners.map((runner) => ({
    id: runner.id,
    skillId: runner.skillId,
    skillActivated: runner.skillActivated,
    skillActivatedAt: runner.skillActivatedAt,
  }));
}

/**
 * 트랙 지오메트리(하늘·관중석 밴드)를 반영한 씬 레이아웃. 레인 영역을 주로 밴드
 * 안쪽으로 한정하며, 프레임 그리기(`renderScene`)와 파티클 원점 계산(`RaceCanvas`)이
 * 동일한 좌표계를 공유하도록 이 함수를 함께 사용한다.
 */
export function computeSceneLayout(state: RaceState, dimensions: Dimensions): RaceLayout {
  const geometry = computeTrackGeometry(dimensions);
  const inset = (geometry.trackBottom - geometry.trackTop) * 0.07;
  return computeRaceLayout(state, dimensions, {
    marginTop: geometry.trackTop + inset,
    marginBottom: dimensions.height - geometry.trackBottom + inset,
  });
}

/**
 * 접전(슬로모션) 구간에서 화면 전체에 적용할 카메라 셰이크 오프셋. `elapsedTime`만으로
 * 결정되는 순수 계산이며(사인 조합), 해당 구간이 아니면 (0, 0)을 반환한다.
 */
export function computeCameraShake(state: RaceState): { x: number; y: number } {
  if (state.finished || !isSlowMotionTriggered(state)) return { x: 0, y: 0 };
  const t = state.elapsedTime;
  return {
    x: Math.sin(t * 57) * CAMERA_SHAKE_AMPLITUDE,
    y: Math.cos(t * 43) * CAMERA_SHAKE_AMPLITUDE * 0.6,
  };
}

/** 종반 접전 연출: 상하 레터박스와 펄스 문구. 슬로모션 구간(미완주)에서만 그린다. */
function drawFinaleCinematics(ctx: RenderContext, dimensions: Dimensions, state: RaceState): void {
  if (state.finished || !isSlowMotionTriggered(state)) return;

  const barHeight = dimensions.height * CINEMATIC_BAR_RATIO;
  ctx.save();

  ctx.globalAlpha = 0.55;
  ctx.fillStyle = "#05070c";
  ctx.fillRect(0, 0, dimensions.width, barHeight);
  ctx.fillRect(0, dimensions.height - barHeight, dimensions.width, barHeight);

  const sorted = [...state.runners].sort((a, b) => b.position - a.position);
  const gap = sorted.length > 1 ? sorted[0].position - sorted[1].position : Number.POSITIVE_INFINITY;
  const label = gap <= TRACK_LENGTH * NECK_AND_NECK_GAP_RATIO ? "대접전!" : "결승선 스퍼트!";

  // 문구는 관중석과 겹치지 않게 주로(잔디) 상단에 배경 패널과 함께 띄운다.
  const geometry = computeTrackGeometry(dimensions);
  const textY = geometry.trackTop + 26;
  const pillWidth = label.length * 22 + 40;

  ctx.globalAlpha = 0.72;
  ctx.fillStyle = "#0c0f14";
  ctx.fillRect(dimensions.width / 2 - pillWidth / 2, textY - 17, pillWidth, 34);

  const pulse = 0.7 + 0.3 * Math.sin(state.elapsedTime * 7);
  ctx.globalAlpha = Math.max(0.4, pulse);
  ctx.fillStyle = "#ffd60a";
  ctx.font = "bold 22px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(label, dimensions.width / 2, textY);

  ctx.globalAlpha = 1;
  ctx.restore();
}

/**
 * 트랙·말·스킬 이펙트·순위표를 그리고, 접전 구간에서는 카메라 셰이크·레터박스 연출을,
 * 완주 상태(`state.finished`)에서는 피니시 배너·우승마 스포트라이트·폭죽 파티클을
 * 이어서 그린다. 파티클(폭죽·먼지) 생성·갱신(수명 관리)은 이 함수의 호출자
 * (`RaceCanvas`)가 소유하는 상태이며, 이 함수는 주어진 파티클 스냅샷을 그리기만 한다.
 */
export function renderScene(
  ctx: RenderContext,
  dimensions: Dimensions,
  state: RaceState,
  runnersMeta: RunnerMeta[],
  particles: FireworkParticle[] = [],
  dustParticles: FireworkParticle[] = [],
): void {
  const layout = computeSceneLayout(state, dimensions);
  const skillRunners = deriveSkillRunners(state);
  const shake = computeCameraShake(state);

  ctx.save();
  ctx.translate(shake.x, shake.y);
  renderRace(ctx, dimensions, layout, runnersMeta, state.elapsedTime, skillRunners, {
    finished: state.finished,
  });
  drawDustParticles(ctx, dustParticles);
  ctx.restore();

  drawFinaleCinematics(ctx, dimensions, state);

  if (!state.finished) return;

  drawFinishBanner(ctx, dimensions, layout, runnersMeta, state);
  drawWinnerSpotlight(ctx, layout, state);
  drawFireworkParticles(ctx, particles, state);
}
