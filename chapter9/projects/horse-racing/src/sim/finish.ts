/** 피니시 근접(슬로모션 트리거)·포토 피니시(접전) 판정을 담당하는 순수 모듈(PRD 4.5). */

import { TRACK_LENGTH } from "./types";
import type { RaceState, RunnerState } from "./types";

/** 선두 진행률(progress)이 이 값 이상이면 슬로모션 트리거가 발동한다. 종반 연출이 늘어지지 않도록 결승선 직전(93%)부터 발동한다. */
export const SLOW_MOTION_PROGRESS_THRESHOLD = 0.93;
/** 완주 시 1위·2위 위치 차가 이 값(트랙 길이 기준) 이하면 포토 피니시(접전)로 판정한다. */
export const PHOTO_FINISH_GAP_THRESHOLD = TRACK_LENGTH * 0.02;

function leaderProgress(runners: RunnerState[]): number {
  const maxPosition = Math.max(...runners.map((runner) => runner.position));
  return maxPosition / TRACK_LENGTH;
}

/** 선두 말의 진행률이 threshold 이상이면 슬로모션 트리거가 필요함을 반환한다. */
export function isSlowMotionTriggered(
  state: RaceState,
  threshold: number = SLOW_MOTION_PROGRESS_THRESHOLD,
): boolean {
  return leaderProgress(state.runners) >= threshold;
}

/** 완주 상태에서 1위·2위 위치 차가 threshold 이하면 포토 피니시(접전)로 판정한다. 미완주면 항상 false다. */
export function isPhotoFinish(
  state: RaceState,
  threshold: number = PHOTO_FINISH_GAP_THRESHOLD,
): boolean {
  if (!state.finished) return false;
  const sorted = [...state.runners].sort((a, b) => b.position - a.position);
  const gap = sorted[0].position - sorted[1].position;
  return gap <= threshold;
}
