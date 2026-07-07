/**
 * `<canvas>`를 마운트해 ctx를 얻고 `createRenderLoop`(T10)를 구동해 매 프레임
 * `renderScene`(T20a)을 그리는 React 컴포넌트. 좌표·순위·발동 이력·파티클 물리는
 * 재구현하지 않고 `src/render`의 기존 함수를 그대로 소비한다. 베팅 확정→경주 생성→
 * 상태 전이→정산→실황 emit의 라이프사이클 오케스트레이션(T20b)과 화면 조립(T20c)은
 * 이 컴포넌트의 몫이 아니며, 이 컴포넌트는 주어진 `initialState`·`machine`으로 loop을
 * 구동해 canvas에 그리는 지점까지만 다룬다.
 */
import { useEffect, useRef } from "react";
import type { HorseProfile } from "../domain/types";
import { createRenderLoop } from "../render/loop";
import {
  createFireworkParticles,
  spawnDustForRunners,
  updateDustParticles,
  updateParticles,
} from "../render/particles";
import { computeSceneLayout, deriveRunnersMeta, renderScene } from "../render/renderScene";
import type {
  Dimensions,
  FireworkParticle,
  RafSource,
  RenderContext,
  RenderLoopMachine,
  VisibilitySource,
} from "../render/types";
import type { RaceState, RankedRunner } from "../sim/types";

const DEFAULT_DIMENSIONS: Dimensions = { width: 1350, height: 690 };

function createBrowserRaf(): RafSource {
  return {
    request: (callback) => window.requestAnimationFrame(callback),
    cancel: (handle) => window.cancelAnimationFrame(handle),
  };
}

function createDocumentVisibility(): VisibilitySource {
  return {
    subscribe(onChange) {
      const handler = () => onChange(document.hidden);
      document.addEventListener("visibilitychange", handler);
      return () => document.removeEventListener("visibilitychange", handler);
    },
  };
}

/**
 * 브라우저 `CanvasRenderingContext2D`를 M4 `RenderContext`로 위임하는 기본 어댑터.
 * 실제 브라우저 ctx는 `RenderContext`가 요구하는 속성·메서드를 구조적으로 이미 만족하므로
 * 캐스팅만으로 위임이 끝난다(별도 래핑 로직 불필요).
 */
function defaultGetContext(canvas: HTMLCanvasElement): RenderContext | null {
  return canvas.getContext("2d") as unknown as RenderContext | null;
}

export interface RaceCanvasProps {
  initialState: RaceState;
  horses: HorseProfile[];
  machine: RenderLoopMachine;
  dimensions?: Dimensions;
  /** 생략 시 `canvas.getContext("2d")`. jsdom은 2d ctx를 구현하지 않으므로 테스트는 mock ctx를 주입한다. */
  getContext?: (canvas: HTMLCanvasElement) => RenderContext | null;
  /** 생략 시 `window.requestAnimationFrame`. 테스트는 가짜 raf를 주입한다. */
  raf?: RafSource;
  /** 생략 시 `document.visibilitychange` 구독. 테스트는 가짜 visibility 소스를 주입한다. */
  visibility?: VisibilitySource;
  /** 생략 시 `Math.random`. 결정적 테스트를 위해 시드 rng를 주입할 수 있다. */
  rng?: () => number;
  /**
   * 매 프레임 루프가 넘기는 상태·순위를 관찰할 콜백(T20b 오케스트레이션 훅이 소비).
   * 렌더링에는 관여하지 않으며, 값이 바뀌어도 loop을 재시작하지 않도록 ref로 최신
   * 값을 참조한다(단일 loop 유지, 무관한 리렌더에서 재시작 방지).
   */
  onFrame?: (state: RaceState, rankings: RankedRunner[]) => void;
}

/**
 * hidden(탭 비활성화) 프레임 렌더 정책: **계속 그린다.** `createRenderLoop`는 hidden
 * 동안에도 매 raf 프레임 `onFrame`을 호출하며(시뮬레이션 전진만 멈춘다), 이때 넘어오는
 * `state`는 직전 프레임과 값이 같으므로 다시 그려도 화면 결과가 달라지지 않아 정책의
 * 이득이 낮다. 이 컴포넌트가 별도로 visibility를 구독해 hidden 플래그로 그리기를
 * 건너뛰지 않는 이유는, 동일 `VisibilitySource`를 loop 내부 구독과 이중 구독하면(단일
 * 리스너만 지원하는 테스트용 mock 등에서) 두 구독이 서로를 덮어써 충돌할 수 있기
 * 때문이다. 가장 단순하고 안전한 선택으로 "유지"를 택한다(되돌리기 쉬운 결정).
 */
export function RaceCanvas(props: RaceCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const dimensions = props.dimensions ?? DEFAULT_DIMENSIONS;
  const { getContext, raf, visibility, rng, machine, initialState, horses } = props;

  const onFrameRef = useRef(props.onFrame);
  onFrameRef.current = props.onFrame;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return undefined;

    const resolvedGetContext = getContext ?? defaultGetContext;
    const ctx = resolvedGetContext(canvas);
    if (!ctx) return undefined;

    const resolvedRaf = raf ?? createBrowserRaf();
    const resolvedVisibility = visibility ?? createDocumentVisibility();
    const resolvedRng = rng ?? Math.random;
    const runnersMeta = deriveRunnersMeta(horses);

    let particles: FireworkParticle[] = [];
    let dustParticles: FireworkParticle[] = [];
    let wasFinished = false;
    /** 완주 후 다음 폭죽까지 남은 시간(초). 축하 연출이 폭죽 1회로 끝나지 않게 주기 발사한다. */
    let fireworkCooldown = 0;

    const loop = createRenderLoop(initialState, {
      raf: resolvedRaf,
      visibility: resolvedVisibility,
      machine,
      rng: resolvedRng,
      onFrame(state, rankings, frameDt) {
        const dt = frameDt ?? 0;

        // 씬과 동일한 좌표계(computeSceneLayout)로 파티클 원점을 계산한다.
        const layout = computeSceneLayout(state, dimensions);
        const winner = layout.leaderboard.find((entry) => entry.rank === 1);
        const winnerPosition = winner
          ? layout.runners.find((runner) => runner.id === winner.id)
          : undefined;

        if (state.finished && !wasFinished && winnerPosition) {
          particles = createFireworkParticles(resolvedRng, winnerPosition.x, winnerPosition.y);
          fireworkCooldown = 0.9;
        }
        wasFinished = state.finished;

        if (particles.length > 0) particles = updateParticles(particles, dt);

        // 완주 이후에는 우승마 주변 하늘에서 소형 폭죽을 주기적으로 이어 쏜다.
        if (state.finished && winnerPosition && dt > 0) {
          fireworkCooldown -= dt;
          if (fireworkCooldown <= 0) {
            const originX = winnerPosition.x + (resolvedRng() - 0.5) * 220;
            const originY = Math.max(30, winnerPosition.y - 40 - resolvedRng() * 90);
            particles = [...particles, ...createFireworkParticles(resolvedRng, originX, originY, 14)];
            fireworkCooldown = 0.85;
          }
        }

        // 달리는 동안 발밑 흙먼지를 생성·갱신한다. 완주 후에는 남은 먼지만 소멸시킨다.
        if (dustParticles.length > 0) dustParticles = updateDustParticles(dustParticles, dt);
        if (!state.finished && dt > 0) {
          dustParticles = [...dustParticles, ...spawnDustForRunners(resolvedRng, layout, dt)];
        }

        renderScene(ctx, dimensions, state, runnersMeta, particles, dustParticles);
        onFrameRef.current?.(state, rankings);
      },
    });

    loop.start();
    return () => {
      loop.stop();
    };
  }, [getContext, raf, visibility, rng, machine, initialState, horses, dimensions]);

  return (
    <canvas
      className="race-canvas"
      ref={canvasRef}
      width={dimensions.width}
      height={dimensions.height}
    />
  );
}
