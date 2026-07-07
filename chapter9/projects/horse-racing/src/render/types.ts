/** T10: 레이아웃 결과 타입과 렌더 루프가 주입받는 인터페이스(raf·visibility·상태 머신 연결). */
import type { RaceState, RankedRunner } from "../sim/types";
import type { GameEvent } from "../store/machine";

export interface Dimensions {
  width: number;
  height: number;
}

export interface RunnerLayout {
  id: string;
  x: number;
  y: number;
}

export interface LeaderboardEntry {
  id: string;
  rank: number;
}

export interface RaceLayout {
  runners: RunnerLayout[];
  leaderboard: LeaderboardEntry[];
  /** 레인 밴드 높이(px). 렌더러가 말 도형 스케일을 정할 때 참조한다. 생략 시 기본 크기로 그린다. */
  laneHeight?: number;
}

/** `requestAnimationFrame`을 주입 가능하게 감싼 인터페이스. 실제 구현은 브라우저 API를 그대로 위임한다. */
export interface RafSource {
  request(callback: (timeMs: number) => void): number;
  cancel(handle: number): void;
}

/** `document.hidden`/`visibilitychange`를 주입 가능하게 감싼 인터페이스. */
export interface VisibilitySource {
  subscribe(onChange: (hidden: boolean) => void): () => void;
}

/** 렌더 루프가 탭 자동 일시정지를 위해 필요로 하는 상태 머신 접근 최소 인터페이스. */
export interface RenderLoopMachine {
  isPaused(): boolean;
  dispatch(event: GameEvent): void;
}

export interface RenderLoopOptions {
  raf: RafSource;
  visibility: VisibilitySource;
  machine: RenderLoopMachine;
  /** 생략 시 Math.random. 결정적 테스트를 위해 시드 rng를 주입할 수 있다. */
  rng?: () => number;
  /** 생략 시 T9의 FIXED_SUBSTEP. */
  fixedStep?: number;
  /**
   * 매 프레임 호출. frameDt는 이번 프레임의 시각 효과용 경과 시간(초, 슬로모션 배율
   * 적용·hidden 프레임은 0)으로, 완주 후 `state.elapsedTime`이 고정된 뒤에도 파티클
   * 갱신에 쓸 수 있다.
   */
  onFrame: (state: RaceState, rankings: RankedRunner[], frameDt: number) => void;
}

export interface RenderLoop {
  start(): void;
  stop(): void;
  getState(): RaceState;
}

/**
 * T11: `CanvasRenderingContext2D`를 얇게 위임할 수 있는 최소 인터페이스.
 * 실제 브라우저 ctx는 구조적으로 이 인터페이스를 만족하므로 그대로 대입 가능하고,
 * 테스트는 DOM 없이 이 인터페이스만 흉내 낸 mock ctx로 호출을 검증한다.
 * (공용 mock은 `src/render/testing.ts`의 `createMockRenderContext`가 제공한다.)
 */
export interface RenderContext {
  fillStyle: string | CanvasGradient | CanvasPattern;
  strokeStyle: string | CanvasGradient | CanvasPattern;
  lineWidth: number;
  font: string;
  textAlign: CanvasTextAlign;
  textBaseline: CanvasTextBaseline;
  globalAlpha: number;
  lineCap: CanvasLineCap;
  fillRect(x: number, y: number, w: number, h: number): void;
  strokeRect(x: number, y: number, w: number, h: number): void;
  clearRect(x: number, y: number, w: number, h: number): void;
  beginPath(): void;
  moveTo(x: number, y: number): void;
  lineTo(x: number, y: number): void;
  quadraticCurveTo(cpx: number, cpy: number, x: number, y: number): void;
  closePath(): void;
  stroke(): void;
  fill(): void;
  arc(x: number, y: number, radius: number, startAngle: number, endAngle: number): void;
  ellipse(
    x: number,
    y: number,
    radiusX: number,
    radiusY: number,
    rotation: number,
    startAngle: number,
    endAngle: number,
  ): void;
  fillText(text: string, x: number, y: number): void;
  setLineDash(segments: number[]): void;
  createLinearGradient(x0: number, y0: number, x1: number, y1: number): CanvasGradient;
  translate(x: number, y: number): void;
  rotate(angle: number): void;
  scale(x: number, y: number): void;
  save(): void;
  restore(): void;
}

/** 렌더러가 색상 외에 번호·이름을 병기하기 위해 필요로 하는 말 메타데이터(PRD 5번·13번). */
export interface RunnerMeta {
  id: string;
  number: number;
  name: string;
  color: string;
}

/** 말 도형(몸통 반지름)과 다리 길이. 레인 밴드 폭이 이 합(HORSE_SHAPE_HEIGHT) 이상이어야 인접 말이 겹치지 않는다. */
export const HORSE_BODY_RADIUS = 8;
export const HORSE_LEG_LENGTH = 10;
export const HORSE_SHAPE_HEIGHT = HORSE_BODY_RADIUS * 2 + HORSE_LEG_LENGTH;

/**
 * 트랙 지오메트리 세로 비율(캔버스 높이 기준). 위에서부터 하늘 → 관중석 → 상단 잔디('
 * 레일 포함) → 주로(레인 영역) → 하단 에이프런 순서로 쌓인다. `computeTrackGeometry`가
 * 이 비율을 픽셀 경계로 변환하며, 레이아웃(`computeSceneLayout`)과 배경 그리기가 공유한다.
 */
export const SKY_BOTTOM_RATIO = 0.1;
export const STAND_BOTTOM_RATIO = 0.24;
export const TRACK_TOP_RATIO = 0.29;
export const TRACK_BOTTOM_RATIO = 0.95;

/** 말 도형의 기준 레인 높이(px). 실제 레인 높이/이 값이 말 스케일이 된다. */
export const HORSE_BASE_LANE_HEIGHT = 34;
/** 말 스케일 클램프 범위. 레인이 아주 넓거나 좁아도 말이 극단적으로 커지거나 작아지지 않게 한다. */
export const HORSE_SCALE_MIN = 0.75;
export const HORSE_SCALE_MAX = 2.25;
/** 갤럽 사이클 각속도(라디안/초). 다리 스윙·몸통 바운스가 이 위상을 공유하며, 경주 체감 속도에 맞춰져 있다. */
export const GALLOP_CYCLE_SPEED = 15;

/** 접전(슬로모션) 구간에서 화면 전체에 적용하는 카메라 셰이크 진폭(px). */
export const CAMERA_SHAKE_AMPLITUDE = 2.4;
/** 접전 연출 레터박스(상하 시네마 바) 높이 비율. */
export const CINEMATIC_BAR_RATIO = 0.055;

/** 달리는 말 뒤에 흩날리는 흙먼지 파티클 상수. */
export const DUST_PARTICLE_LIFESPAN = 0.55;
export const DUST_PARTICLE_BASE_RADIUS = 1.8;
export const DUST_PARTICLE_COLOR = "#cdb693";
/** 초당 말 1마리가 만드는 먼지 퍼프 기대 횟수. */
export const DUST_SPAWN_RATE = 9;

/**
 * 스킬 발동 이펙트·배너가 노출되는 지속 창(초). 발동 시점(`skillActivatedAt`)부터
 * 이 값 이내(양 끝 포함)의 `elapsedTime`에서만 이펙트를 그린다. sim의 스킬별
 * 실제 효과 지속(`SKILL_CONFIG.duration`, 2~6초)과는 독립된 렌더 레이어 고유
 * 상수다(sim 내부 설정을 참조하지 않는다).
 */
export const SKILL_EFFECT_DURATION = 1.2;

/** 발동 이력·표시할 스킬을 함께 실어 이펙트/배너 렌더에 필요한 최소 러너 정보(T12). */
export interface SkillActivationInfo {
  id: string;
  skillId?: string;
  skillActivated?: boolean;
  skillActivatedAt?: number | null;
}

/** 슬로모션 트리거(`isSlowMotionTriggered`) 시 렌더 루프가 dt에 곱하는 배율(PRD 4.5, T13). 지나치게 늘어지지 않도록 0.45로 유지한다. */
export const SLOW_MOTION_TIME_SCALE = 0.45;

/** 폭죽 파티클 하나의 물리 상태(위치·속도·잔여 수명). 생성은 rng로, 갱신은 dt만으로 결정된다(T14). */
export interface FireworkParticle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  remaining: number;
  max: number;
}

/** 결승선 통과 시 생성하는 폭죽 파티클 수(T14). */
export const FIREWORK_PARTICLE_COUNT = 24;
/** 파티클 수명(초). */
export const FIREWORK_PARTICLE_LIFESPAN = 1.2;
/** 파티클 초기 속력 범위(px/s). */
export const FIREWORK_SPEED_MIN = 60;
export const FIREWORK_SPEED_MAX = 160;
/** 파티클에 적용되는 중력 가속도(px/s^2). 위로 솟았다가 떨어지는 궤적을 만든다. */
export const FIREWORK_GRAVITY = 120;
export const FIREWORK_PARTICLE_RADIUS = 2.5;
/** 폭죽 파티클 팔레트. 파티클 인덱스 순환으로 색을 섞어 단색 폭죽보다 축제감을 높인다. */
export const FIREWORK_PARTICLE_COLORS = ["#ffd60a", "#ff5d8f", "#4cc9f0", "#80ed99", "#ff9e00"];

/** 우승마 스포트라이트 반지름·색상(T14). 좌표는 layout에서만 가져온다. */
export const WINNER_SPOTLIGHT_RADIUS = HORSE_BODY_RADIUS * 4;
export const WINNER_SPOTLIGHT_COLOR = "rgba(255, 251, 230, 0.35)";
