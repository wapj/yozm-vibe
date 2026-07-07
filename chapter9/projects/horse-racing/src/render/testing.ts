/**
 * 테스트 전용 공용 mock `RenderContext`. 렌더 계열 테스트 7곳에 흩어져 있던 동일한
 * mock 정의를 한 곳으로 모아, `RenderContext` 인터페이스가 확장될 때 이 파일만
 * 갱신하면 되게 한다. 프로덕션 코드는 이 모듈을 import하지 않는다.
 */
import { vi } from "vitest";
import type { RenderContext } from "./types";

/** `addColorStop`만 흉내 낸 가짜 CanvasGradient. fillStyle에 그대로 대입할 수 있다. */
function createMockGradient(): CanvasGradient {
  return { addColorStop: vi.fn() } as unknown as CanvasGradient;
}

export function createMockRenderContext(): RenderContext {
  return {
    fillStyle: "",
    strokeStyle: "",
    lineWidth: 1,
    font: "",
    textAlign: "left",
    textBaseline: "alphabetic",
    globalAlpha: 1,
    lineCap: "butt",
    fillRect: vi.fn(),
    strokeRect: vi.fn(),
    clearRect: vi.fn(),
    beginPath: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    quadraticCurveTo: vi.fn(),
    closePath: vi.fn(),
    stroke: vi.fn(),
    fill: vi.fn(),
    arc: vi.fn(),
    ellipse: vi.fn(),
    fillText: vi.fn(),
    setLineDash: vi.fn(),
    createLinearGradient: vi.fn(() => createMockGradient()),
    translate: vi.fn(),
    rotate: vi.fn(),
    scale: vi.fn(),
    save: vi.fn(),
    restore: vi.fn(),
  };
}
