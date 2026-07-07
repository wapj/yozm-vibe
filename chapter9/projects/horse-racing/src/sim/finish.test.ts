import { describe, expect, it } from "vitest";
import { isPhotoFinish, isSlowMotionTriggered, PHOTO_FINISH_GAP_THRESHOLD } from "./finish";
import { TRACK_LENGTH } from "./types";
import type { RaceState, RunnerState } from "./types";

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

function makeState(positions: number[], finished: boolean): RaceState {
  return {
    runners: positions.map((position, index) => makeRunner(`horse-${index + 1}`, position)),
    elapsedTime: 10,
    finished,
  };
}

describe("isSlowMotionTriggered", () => {
  it("선두 진행률이 임계값 이상이면 true를 반환한다", () => {
    const state = makeState([TRACK_LENGTH * 0.95, TRACK_LENGTH * 0.8], false);
    expect(isSlowMotionTriggered(state, 0.9)).toBe(true);
  });

  it("선두 진행률이 임계값 미만이면 false를 반환한다", () => {
    const state = makeState([TRACK_LENGTH * 0.85, TRACK_LENGTH * 0.7], false);
    expect(isSlowMotionTriggered(state, 0.9)).toBe(false);
  });

  it("선두 진행률이 임계값과 정확히 같으면 true를 반환한다(경계값)", () => {
    const state = makeState([TRACK_LENGTH * 0.9, TRACK_LENGTH * 0.5], false);
    expect(isSlowMotionTriggered(state, 0.9)).toBe(true);
  });
});

describe("isPhotoFinish", () => {
  it("완주 상태에서 1위·2위 위치 차가 임계값 이내면 true를 반환한다", () => {
    const state = makeState([TRACK_LENGTH, TRACK_LENGTH - 10, TRACK_LENGTH - 200], true);
    expect(isPhotoFinish(state, 20)).toBe(true);
  });

  it("완주 상태에서 1위·2위 위치 차가 임계값을 초과하면 false를 반환한다", () => {
    const state = makeState([TRACK_LENGTH, TRACK_LENGTH - 50, TRACK_LENGTH - 200], true);
    expect(isPhotoFinish(state, 20)).toBe(false);
  });

  it("1위·2위 위치 차가 임계값과 정확히 같으면 true를 반환한다(경계값)", () => {
    const state = makeState([TRACK_LENGTH, TRACK_LENGTH - 20, TRACK_LENGTH - 200], true);
    expect(isPhotoFinish(state, 20)).toBe(true);
  });

  it("미완주 상태에서는 위치 차와 무관하게 false를 반환한다", () => {
    const state = makeState([TRACK_LENGTH * 0.5, TRACK_LENGTH * 0.5 - 1], false);
    expect(isPhotoFinish(state, 20)).toBe(false);
  });

  it("기본 임계값(PHOTO_FINISH_GAP_THRESHOLD)으로도 판정할 수 있다", () => {
    const state = makeState([TRACK_LENGTH, TRACK_LENGTH - PHOTO_FINISH_GAP_THRESHOLD], true);
    expect(isPhotoFinish(state)).toBe(true);
  });
});
