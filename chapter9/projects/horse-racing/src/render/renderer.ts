/**
 * T10 `computeRaceLayout` 좌표를 소비하는 실제 Canvas 2D 렌더러(T11).
 * 좌표 계산(진행률→x, 레인→y, 순위 산출)은 재구현하지 않고, 주입된 ctx에
 * 경마장 배경(하늘·관중석·잔디 주로·게이트·체크무늬 결승선)과 갤럽하는 말
 * (몸통·목·머리·다리 4개·꼬리·기수 실루엣), 순위표(번호·이름 병기)를 그린다.
 */
import { TRACK_LENGTH } from "../sim/types";
import { renderSkillEffects } from "./effects";
import {
  GALLOP_CYCLE_SPEED,
  HORSE_BASE_LANE_HEIGHT,
  HORSE_SCALE_MAX,
  HORSE_SCALE_MIN,
  SKY_BOTTOM_RATIO,
  STAND_BOTTOM_RATIO,
  TRACK_BOTTOM_RATIO,
  TRACK_TOP_RATIO,
} from "./types";
import type { Dimensions, RaceLayout, RenderContext, RunnerMeta, SkillActivationInfo } from "./types";

/** 트랙 시각 요소(게이트·결승선)의 화면 여백 비율. 러너 좌표는 layout에서 그대로 소비하며, 이 비율은 배경 그림에만 쓰인다. */
const TRACK_VISUAL_MARGIN_RATIO = 0.05;

const DEFAULT_RUNNER_COLOR = "#888888";

/** 하늘·관중석·잔디 팔레트. */
const SKY_TOP_COLOR = "#6cb7dd";
const SKY_BOTTOM_COLOR = "#d3ecf7";
const STAND_ROOF_COLOR = "#37474f";
const STAND_BAND_COLOR = "#5d4f45";
const RAIL_COLOR = "#f6f7f4";
const APRON_GRASS_COLOR = "#3c8038";
const TRACK_GRASS_TOP = "#58a44b";
const TRACK_GRASS_BOTTOM = "#4a9440";
const CROWD_PALETTE = ["#f2d0a4", "#e8a87c", "#f7ef99", "#9ad1d4", "#f4989c", "#c8b6ff", "#ffffff"];

const LEADERBOARD_ORIGIN_X = 12;
const LEADERBOARD_ORIGIN_Y = 12;
const LEADERBOARD_ROW_HEIGHT = 17;
const LEADERBOARD_RANK_COLORS = ["#ffd60a", "#e8e8e8", "#dd9e5b"];

export interface TrackBounds {
  startX: number;
  finishX: number;
}

/** 배경 밴드(하늘·관중석·주로)의 픽셀 경계. 배경 그리기와 씬 레이아웃(marginTop 산출)이 공유한다. */
export interface TrackGeometry extends TrackBounds {
  skyBottom: number;
  standBottom: number;
  trackTop: number;
  trackBottom: number;
}

/** 트랙 배경(게이트·결승선)을 그릴 x좌표 범위. 좌 출발·우 결승 순서를 고정한다. */
export function computeTrackBounds(dimensions: Dimensions): TrackBounds {
  const marginX = dimensions.width * TRACK_VISUAL_MARGIN_RATIO;
  return { startX: marginX, finishX: dimensions.width - marginX };
}

export function computeTrackGeometry(dimensions: Dimensions): TrackGeometry {
  return {
    ...computeTrackBounds(dimensions),
    skyBottom: dimensions.height * SKY_BOTTOM_RATIO,
    standBottom: dimensions.height * STAND_BOTTOM_RATIO,
    trackTop: dimensions.height * TRACK_TOP_RATIO,
    trackBottom: dimensions.height * TRACK_BOTTOM_RATIO,
  };
}

function metaById(runnersMeta: RunnerMeta[]): Map<string, RunnerMeta> {
  return new Map(runnersMeta.map((meta) => [meta.id, meta]));
}

/** 시드 없는 결정적 의사난수(0~1). 관중 점 배치처럼 프레임마다 같아야 하는 장식에 쓴다. */
function hash01(n: number): number {
  const s = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return s - Math.floor(s);
}

/** #rrggbb 색을 밝게(amount>0) 또는 어둡게(amount<0) 섞은 색을 반환한다. */
export function shadeColor(hex: string, amount: number): string {
  const raw = hex.replace("#", "");
  const full = raw.length === 3 ? raw.split("").map((c) => c + c).join("") : raw;
  const num = parseInt(full, 16);
  if (Number.isNaN(num) || full.length !== 6) return hex;
  const channels = [(num >> 16) & 0xff, (num >> 8) & 0xff, num & 0xff].map((channel) => {
    const target = amount >= 0 ? 255 : 0;
    const mixed = channel + (target - channel) * Math.min(1, Math.abs(amount));
    return Math.round(Math.max(0, Math.min(255, mixed)));
  });
  return `#${channels.map((channel) => channel.toString(16).padStart(2, "0")).join("")}`;
}

export interface DrawTrackOptions {
  /** 레인 구분선을 그릴 레인 수. 생략 시 레인 구분선을 생략한다. */
  laneCount?: number;
  /** 관중 웨이브 등 배경 장식 애니메이션에 쓰는 경과 시간(초). */
  frameTime?: number;
}

function drawSky(ctx: RenderContext, dimensions: Dimensions, standBottom: number): void {
  const gradient = ctx.createLinearGradient(0, 0, 0, standBottom);
  gradient.addColorStop(0, SKY_TOP_COLOR);
  gradient.addColorStop(1, SKY_BOTTOM_COLOR);
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, dimensions.width, standBottom);
}

function drawStands(ctx: RenderContext, dimensions: Dimensions, geometry: TrackGeometry, frameTime: number): void {
  const { skyBottom, standBottom } = geometry;
  const bandHeight = standBottom - skyBottom;

  // 지붕과 관중 밴드.
  ctx.fillStyle = STAND_ROOF_COLOR;
  ctx.fillRect(0, skyBottom - bandHeight * 0.28, dimensions.width, bandHeight * 0.28);
  ctx.fillStyle = STAND_BAND_COLOR;
  ctx.fillRect(0, skyBottom, dimensions.width, bandHeight);

  // 관중: 결정적 배치의 점들. 크기·위치를 흩뜨리고 웨이브로 소란스러운 분위기를 만든다.
  const rows = 4;
  const spacing = 7;
  const columns = Math.ceil(dimensions.width / spacing);
  for (let row = 0; row < rows; row += 1) {
    const baseY = skyBottom + bandHeight * (0.24 + row * 0.2);
    for (let column = 0; column < columns; column += 1) {
      const seed = row * 1000 + column;
      const jitterX = (hash01(seed) - 0.5) * 6;
      const jitterY = (hash01(seed + 5.3) - 0.5) * 4;
      const wave = Math.sin(frameTime * 2.6 + column * 0.4 + row * 1.3) * 1.3;
      ctx.fillStyle = CROWD_PALETTE[Math.floor(hash01(seed + 0.5) * CROWD_PALETTE.length) % CROWD_PALETTE.length];
      ctx.beginPath();
      ctx.arc(column * spacing + jitterX + 3, baseY + jitterY + wave, 1.2 + hash01(seed + 2.7) * 1.1, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // 관중석과 주로를 나누는 흰 레일 두 줄.
  ctx.fillStyle = RAIL_COLOR;
  ctx.fillRect(0, standBottom, dimensions.width, 2.5);
  ctx.fillRect(0, standBottom + 5, dimensions.width, 1.5);
}

function drawGrassCourse(
  ctx: RenderContext,
  dimensions: Dimensions,
  geometry: TrackGeometry,
  laneCount?: number,
): void {
  const { standBottom, trackTop, trackBottom } = geometry;

  // 레일 아래 상단 잔디 스트립 + 주로 본체(세로 그라데이션).
  ctx.fillStyle = APRON_GRASS_COLOR;
  ctx.fillRect(0, standBottom, dimensions.width, trackTop - standBottom);
  const gradient = ctx.createLinearGradient(0, trackTop, 0, trackBottom);
  gradient.addColorStop(0, TRACK_GRASS_TOP);
  gradient.addColorStop(1, TRACK_GRASS_BOTTOM);
  ctx.fillStyle = gradient;
  ctx.fillRect(0, trackTop, dimensions.width, trackBottom - trackTop);

  // 모잉 스트라이프: 세로 밴드를 교차로 밝게 깔아 잔디 결을 만든다.
  const stripeWidth = dimensions.width / 12;
  ctx.fillStyle = "rgba(255, 255, 255, 0.05)";
  for (let x = 0; x < dimensions.width; x += stripeWidth * 2) {
    ctx.fillRect(x, trackTop, stripeWidth, trackBottom - trackTop);
  }

  // 레인 구분 점선.
  if (laneCount && laneCount > 1) {
    ctx.save();
    ctx.strokeStyle = "rgba(255, 255, 255, 0.28)";
    ctx.lineWidth = 1;
    ctx.setLineDash([9, 13]);
    const laneHeight = (trackBottom - trackTop) / laneCount;
    for (let lane = 1; lane < laneCount; lane += 1) {
      const y = trackTop + laneHeight * lane;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(dimensions.width, y);
      ctx.stroke();
    }
    ctx.setLineDash([]);
    ctx.restore();
  }

  // 하단 에이프런 잔디 + 레일.
  ctx.fillStyle = APRON_GRASS_COLOR;
  ctx.fillRect(0, trackBottom, dimensions.width, dimensions.height - trackBottom);
  ctx.fillStyle = RAIL_COLOR;
  ctx.fillRect(0, trackBottom, dimensions.width, 2);
}

function drawDistanceMarkers(ctx: RenderContext, geometry: TrackGeometry): void {
  const { startX, finishX, trackTop, trackBottom } = geometry;
  ctx.save();
  for (const fraction of [0.25, 0.5, 0.75]) {
    const x = startX + fraction * (finishX - startX);

    ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([7, 11]);
    ctx.beginPath();
    ctx.moveTo(x, trackTop);
    ctx.lineTo(x, trackBottom);
    ctx.stroke();
    ctx.setLineDash([]);

    // 상단 거리 표지판(트랙 길이 1000 기준 250/500/750).
    ctx.fillStyle = "rgba(255, 255, 255, 0.88)";
    ctx.fillRect(x - 13, trackTop - 15, 26, 12);
    ctx.fillStyle = "#274c1f";
    ctx.font = "bold 9px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(String(Math.round(TRACK_LENGTH * fraction)), x, trackTop - 9);
  }
  ctx.restore();
}

function drawStartGate(ctx: RenderContext, geometry: TrackGeometry): void {
  const { startX, trackTop, trackBottom } = geometry;
  ctx.save();

  ctx.strokeStyle = "#20242a";
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(startX, trackTop - 6);
  ctx.lineTo(startX, trackBottom);
  ctx.stroke();

  ctx.fillStyle = "#20242a";
  ctx.fillRect(startX - 24, trackTop - 22, 48, 15);
  ctx.fillStyle = "#f4f4f4";
  ctx.font = "bold 9px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("START", startX, trackTop - 14.5);

  ctx.restore();
}

function drawFinishLine(ctx: RenderContext, geometry: TrackGeometry): void {
  const { finishX, trackTop, trackBottom } = geometry;
  const cell = 6;
  const columns = 2;
  ctx.save();

  // 체크무늬 밴드.
  for (let column = 0; column < columns; column += 1) {
    for (let y = trackTop, row = 0; y < trackBottom; y += cell, row += 1) {
      ctx.fillStyle = (row + column) % 2 === 0 ? "#ffffff" : "#16181d";
      ctx.fillRect(finishX + column * cell - cell, y, cell, Math.min(cell, trackBottom - y));
    }
  }

  ctx.fillStyle = "#c0262d";
  ctx.fillRect(finishX - 27, trackTop - 22, 54, 15);
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 9px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("FINISH", finishX, trackTop - 14.5);

  ctx.restore();
}

/** 경마장 배경 전체(하늘·관중석·잔디 주로·거리 마커·게이트·결승선)를 그린다. */
export function drawTrack(ctx: RenderContext, dimensions: Dimensions, options?: DrawTrackOptions): void {
  const geometry = computeTrackGeometry(dimensions);
  const frameTime = options?.frameTime ?? 0;

  drawSky(ctx, dimensions, geometry.standBottom);
  drawStands(ctx, dimensions, geometry, frameTime);
  drawGrassCourse(ctx, dimensions, geometry, options?.laneCount);
  drawDistanceMarkers(ctx, geometry);
  drawStartGate(ctx, geometry);
  drawFinishLine(ctx, geometry);
}

interface HorsePose {
  /** 갤럽 위상(라디안). 다리 스윙·바운스가 공유한다. */
  phase: number;
  /** 정지 자세(완주 후) 여부. true면 스윙·바운스를 멈추고 서 있는 자세로 그린다. */
  standing: boolean;
}

/** 다리 하나를 허벅지→무릎(제어점)→발굽의 곡선으로 그린다. bendDir: 앞다리 +1, 뒷다리 -1. */
function drawLeg(
  ctx: RenderContext,
  hipX: number,
  hipY: number,
  theta: number,
  bendDir: number,
  standing: boolean,
): void {
  const stride = standing ? bendDir * 1.2 : Math.sin(theta) * 5.4;
  const lift = standing ? 0 : Math.max(0, -Math.cos(theta)) * 3.6;
  const hoofX = hipX + stride;
  const hoofY = 13 - lift;
  const kneeX = (hipX + hoofX) / 2 + bendDir * (standing ? 1 : 2.6);
  const kneeY = hipY + (hoofY - hipY) * 0.45;

  ctx.beginPath();
  ctx.moveTo(hipX, hipY);
  ctx.quadraticCurveTo(kneeX, kneeY, hoofX, hoofY);
  ctx.stroke();

  // 발굽.
  ctx.beginPath();
  ctx.moveTo(hoofX - 1, hoofY + 0.6);
  ctx.lineTo(hoofX + 1.4, hoofY + 0.6);
  ctx.stroke();
}

/**
 * 원점(몸통 중심)에 오른쪽을 향해 달리는 경주마 한 마리를 그린다.
 * 호출자가 translate/scale로 위치·크기를 잡은 로컬 좌표계(기준 폭 약 36px)를 가정한다.
 */
export function drawHorse(ctx: RenderContext, color: string, pose: HorsePose, number?: number): void {
  const dark = shadeColor(color, -0.35);
  const darker = shadeColor(color, -0.55);
  const silk = shadeColor(color, 0.55);
  const { phase, standing } = pose;

  // 원위(화면 반대편) 다리 2개: 어둡게, 몸통 뒤에 깔린다.
  ctx.strokeStyle = darker;
  ctx.lineWidth = 2.2;
  ctx.lineCap = "round";
  drawLeg(ctx, -6.2, 2.6, phase + Math.PI * 0.92 + 0.5, -1, standing);
  drawLeg(ctx, 6.4, 2.6, phase + 0.5, 1, standing);

  // 꼬리: 뒤로 흐르는 세 가닥. 달리는 동안 끝이 나부낀다.
  ctx.strokeStyle = darker;
  ctx.lineWidth = 1.7;
  for (let strand = 0; strand < 3; strand += 1) {
    const wag = standing ? 0 : Math.sin(phase * 0.9 + strand * 0.9) * 1.6;
    ctx.beginPath();
    ctx.moveTo(-9.8, -2.6);
    ctx.quadraticCurveTo(-13.5, -4.2 + strand * 1.3, -16.5, -4.6 + strand * 2 + wag);
    ctx.stroke();
  }

  // 몸통(엉덩이·몸통·가슴 타원 세 개로 볼륨을 만든다).
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.ellipse(-6.3, -0.9, 4.9, 4.5, 0.08, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.ellipse(0, 0, 10.4, 5, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.ellipse(6.4, 0.4, 4.6, 4.3, -0.1, 0, Math.PI * 2);
  ctx.fill();

  // 목: 어깨에서 앞위로 뻗는 사변형 곡선.
  ctx.beginPath();
  ctx.moveTo(3.6, -3.4);
  ctx.quadraticCurveTo(8.2, -6.2, 11.4, -9.6);
  ctx.lineTo(14.9, -7);
  ctx.quadraticCurveTo(10.6, -3, 8, 1.6);
  ctx.closePath();
  ctx.fill();

  // 머리: 앞으로 뻗은 회전 타원 + 주둥이.
  ctx.beginPath();
  ctx.ellipse(13.6, -8.2, 3.4, 1.95, 0.42, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = dark;
  ctx.beginPath();
  ctx.ellipse(16.2, -6.7, 1.7, 1.15, 0.42, 0, Math.PI * 2);
  ctx.fill();

  // 귀·눈.
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(11.4, -10.6);
  ctx.lineTo(12.2, -13.1);
  ctx.lineTo(13.5, -10.7);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = "#ffffff";
  ctx.beginPath();
  ctx.arc(13.7, -9.1, 0.95, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#16181d";
  ctx.beginPath();
  ctx.arc(13.9, -9.1, 0.5, 0, Math.PI * 2);
  ctx.fill();

  // 갈기: 목 능선을 따라 어두운 곡선 두 줄.
  ctx.strokeStyle = darker;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(11.2, -10.4);
  ctx.quadraticCurveTo(7.4, -8, 4.4, -4.2);
  ctx.stroke();
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  ctx.moveTo(10.6, -9);
  ctx.quadraticCurveTo(7.6, -6.6, 5.6, -3.4);
  ctx.stroke();

  // 근위(화면 쪽) 다리 2개: 본색보다 살짝 어둡게, 몸통 위에 겹친다.
  ctx.strokeStyle = dark;
  ctx.lineWidth = 2.5;
  drawLeg(ctx, -6.4, 3, phase + Math.PI * 0.92, -1, standing);
  drawLeg(ctx, 6.6, 3, phase, 1, standing);

  // 안장보: 흰 바탕에 말 번호를 병기해 색 이외의 식별 수단을 제공한다(PRD 5번·13번).
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(-1.2, -4.9, 5, 6);
  ctx.strokeStyle = dark;
  ctx.lineWidth = 0.8;
  ctx.strokeRect(-1.2, -4.9, 5, 6);
  if (number !== undefined) {
    ctx.fillStyle = "#16181d";
    ctx.font = "bold 5px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(String(number), 1.3, -1.8);
  }

  // 기수: 웅크린 몸(실크색)·헬멧·고삐 잡은 팔.
  ctx.fillStyle = silk;
  ctx.beginPath();
  ctx.ellipse(0.6, -7.7, 3, 2.3, -0.55, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.arc(3.7, -9.9, 1.85, 0, Math.PI * 2);
  ctx.fillStyle = "#f6f3ec";
  ctx.fill();
  ctx.strokeStyle = silk;
  ctx.lineWidth = 1.3;
  ctx.beginPath();
  ctx.moveTo(2.4, -7.6);
  ctx.quadraticCurveTo(5.4, -6.8, 7.6, -5.6);
  ctx.stroke();
}

/**
 * 각 러너를 layout의 (x, y) 좌표에 갤럽 애니메이션(다리 스윙·몸통 바운스·피치)과 함께
 * 그린다. frameTime(초 단위 진행 시간)에 따라 위상이 진행되어 정지 화면이 되지 않는다.
 */
export function drawRunners(
  ctx: RenderContext,
  layout: RaceLayout,
  runnersMeta: RunnerMeta[],
  frameTime: number,
  options?: { finished?: boolean },
): void {
  const metaMap = metaById(runnersMeta);
  const standing = options?.finished ?? false;
  const scale = Math.min(
    HORSE_SCALE_MAX,
    Math.max(HORSE_SCALE_MIN, (layout.laneHeight ?? HORSE_BASE_LANE_HEIGHT) / HORSE_BASE_LANE_HEIGHT),
  );

  layout.runners.forEach((runner, index) => {
    const meta = metaMap.get(runner.id);
    const color = meta?.color ?? DEFAULT_RUNNER_COLOR;
    /** 러너마다 위상을 달리해 다리가 같은 박자로 움직이지 않게 한다. */
    const phase = frameTime * GALLOP_CYCLE_SPEED + index * 1.7;
    const bounce = standing ? 0 : Math.abs(Math.sin(phase)) * 2.1;
    const pitch = standing ? 0 : Math.sin(phase + 0.55) * 0.055;

    ctx.save();
    ctx.translate(runner.x, runner.y);
    ctx.scale(scale, scale);

    // 지면 그림자: 바운스가 클수록 살짝 작아져 공중감을 준다.
    ctx.globalAlpha = 0.17;
    ctx.fillStyle = "#10241a";
    ctx.beginPath();
    ctx.ellipse(0, 14.6, 12 - bounce * 0.7, 2.4, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;

    // 스피드 라인: 달리는 동안 몸 뒤로 흐르는 잔상.
    if (!standing) {
      ctx.strokeStyle = "#ffffff";
      ctx.globalAlpha = 0.3;
      ctx.lineWidth = 1.1;
      ctx.lineCap = "round";
      for (let line = 0; line < 3; line += 1) {
        const length = 7 + Math.sin(phase * 1.3 + line * 2.1) * 2.5;
        const y = -4 + line * 3.6;
        ctx.beginPath();
        ctx.moveTo(-12.5, y);
        ctx.lineTo(-12.5 - length, y);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
    }

    ctx.translate(0, -bounce);
    ctx.rotate(pitch);
    drawHorse(ctx, color, { phase, standing }, meta?.number);

    ctx.restore();
  });
}

/**
 * leaderboard 순서대로 순위·번호·이름을 반투명 패널 위에 그린다. 1~3위는 금·은·동색으로
 * 강조하고, 색상만으로 말을 구분하지 않도록 텍스트로 번호·이름을 병기한다(PRD 5번·13번).
 */
export function drawLeaderboard(ctx: RenderContext, layout: RaceLayout, runnersMeta: RunnerMeta[]): void {
  const metaMap = metaById(runnersMeta);
  const rows = layout.leaderboard.length;
  if (rows === 0) return;

  ctx.save();

  ctx.globalAlpha = 0.78;
  ctx.fillStyle = "#0c0f14";
  ctx.fillRect(LEADERBOARD_ORIGIN_X - 4, LEADERBOARD_ORIGIN_Y - 4, 172, rows * LEADERBOARD_ROW_HEIGHT + 8);
  ctx.globalAlpha = 1;

  ctx.font = "bold 12px sans-serif";
  ctx.textAlign = "left";
  ctx.textBaseline = "top";

  layout.leaderboard.forEach((entry, index) => {
    const meta = metaMap.get(entry.id);
    const rowY = LEADERBOARD_ORIGIN_Y + index * LEADERBOARD_ROW_HEIGHT;

    if (meta) {
      ctx.fillStyle = meta.color;
      ctx.fillRect(LEADERBOARD_ORIGIN_X + 16, rowY + 2, 9, 9);
    }

    // 순위 숫자는 스와치 왼쪽, 번호·이름은 스와치 오른쪽에 그린다. meta가 없으면 순위만 남긴다.
    ctx.fillStyle = LEADERBOARD_RANK_COLORS[entry.rank - 1] ?? "#f2f2f2";
    ctx.fillText(String(entry.rank), LEADERBOARD_ORIGIN_X, rowY);
    if (meta) ctx.fillText(`${meta.number}번 ${meta.name}`, LEADERBOARD_ORIGIN_X + 30, rowY);
  });

  ctx.restore();
}

export interface RenderRaceOptions {
  /** 완주 여부. true면 말이 정지 자세로 전환된다. */
  finished?: boolean;
}

/** 트랙·말·스킬 이펙트·순위표를 한 프레임 분 순서대로 그리는 진입점. */
export function renderRace(
  ctx: RenderContext,
  dimensions: Dimensions,
  layout: RaceLayout,
  runnersMeta: RunnerMeta[],
  frameTime: number,
  skillRunners: SkillActivationInfo[] = [],
  options?: RenderRaceOptions,
): void {
  drawTrack(ctx, dimensions, { laneCount: layout.runners.length, frameTime });
  drawRunners(ctx, layout, runnersMeta, frameTime, { finished: options?.finished });
  renderSkillEffects(ctx, layout, skillRunners, frameTime);
  drawLeaderboard(ctx, layout, runnersMeta);
}
