/**
 * 시뮬레이션 상태(각 말의 진행률/위치)를 화면 좌표로 매핑하는 순수 레이아웃 함수(T10).
 * DOM·Canvas ctx를 참조하지 않으며, 실제 그리기는 T11이 이 좌표를 소비한다.
 */
import { rankRunners } from "../sim/engine";
import { TRACK_LENGTH, type RaceState } from "../sim/types";
import type { Dimensions, RaceLayout } from "./types";

/** 캔버스 가로/세로 여백 비율. 트랙 시작·끝과 레인 상하단에 여유를 둔다. */
const DEFAULT_MARGIN_RATIO = 0.05;

export interface ComputeRaceLayoutOptions {
  marginX?: number;
  marginY?: number;
  /** 상하 비대칭 여백. 지정 시 marginY보다 우선한다(관중석 등 상단 배경 영역 확보용). */
  marginTop?: number;
  marginBottom?: number;
}

/**
 * 각 말의 진행률(position/TRACK_LENGTH)을 출발선~결승선 사이 x좌표로 단조 매핑하고,
 * 러너 수만큼 레인 y를 겹치지 않게 등분하며, 순위표를 현재 순위 순서로 산출한다.
 */
export function computeRaceLayout(
  state: RaceState,
  dimensions: Dimensions,
  options?: ComputeRaceLayoutOptions,
): RaceLayout {
  const marginX = options?.marginX ?? dimensions.width * DEFAULT_MARGIN_RATIO;
  const marginY = options?.marginY ?? dimensions.height * DEFAULT_MARGIN_RATIO;
  const marginTop = options?.marginTop ?? marginY;
  const marginBottom = options?.marginBottom ?? marginY;

  const startX = marginX;
  const finishX = dimensions.width - marginX;
  const laneCount = state.runners.length;
  const laneHeight = laneCount > 0 ? (dimensions.height - marginTop - marginBottom) / laneCount : 0;

  const runners = state.runners.map((runner, index) => {
    const progress = Math.min(1, Math.max(0, runner.position / TRACK_LENGTH));
    return {
      id: runner.id,
      x: startX + progress * (finishX - startX),
      y: marginTop + laneHeight * index + laneHeight / 2,
    };
  });

  const leaderboard = rankRunners(state.runners).map((ranked) => ({
    id: ranked.id,
    rank: ranked.rank,
  }));

  return { runners, leaderboard, laneHeight };
}
