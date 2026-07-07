import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { HorseProfile } from "../domain/types";
import { BetPanel } from "./BetPanel";

afterEach(cleanup);

const HORSES: HorseProfile[] = [
  {
    id: "horse-1",
    number: 1,
    name: "번개질주",
    color: "#e63946",
    personality: "저돌적",
    baseStats: { speed: 88, stamina: 60, burst: 70, luck: 45 },
    skill: { id: "start-dash", name: "스타트 대시", description: "" },
  },
  {
    id: "horse-2",
    number: 2,
    name: "질풍",
    color: "#457b9d",
    personality: "차분함",
    baseStats: { speed: 70, stamina: 80, burst: 60, luck: 55 },
    skill: { id: "last-spurt", name: "라스트 스퍼트", description: "" },
  },
];

function selectHorse(name: string): void {
  fireEvent.click(screen.getByLabelText(name));
}

function setDirectAmount(value: string): void {
  fireEvent.change(screen.getByLabelText("직접 입력"), { target: { value } });
}

function isDisabled(text: string): boolean {
  return (screen.getByText(text) as HTMLButtonElement).disabled;
}

describe("BetPanel", () => {
  it("말 미선택이면 확정 버튼이 비활성이다", () => {
    render(<BetPanel horses={HORSES} balance={10000} onConfirm={vi.fn()} />);

    setDirectAmount("500");

    expect(isDisabled("베팅 확정")).toBe(true);
  });

  it("무효 금액이면 확정 버튼이 비활성이다", () => {
    render(<BetPanel horses={HORSES} balance={10000} onConfirm={vi.fn()} />);

    selectHorse("1번 번개질주");
    setDirectAmount("50");

    expect(isDisabled("베팅 확정")).toBe(true);
  });

  it("유효한 선택·금액이면 확정 콜백이 선택 말 id·금액 인자로 1회 호출된다", () => {
    const onConfirm = vi.fn();
    render(<BetPanel horses={HORSES} balance={10000} onConfirm={onConfirm} />);

    selectHorse("2번 질풍");
    setDirectAmount("500");
    fireEvent.click(screen.getByText("베팅 확정"));

    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onConfirm).toHaveBeenCalledWith("horse-2", 500);
  });

  it("올인 선택 시 금액이 현재 잔고와 일치한다", () => {
    const onConfirm = vi.fn();
    render(<BetPanel horses={HORSES} balance={3200} onConfirm={onConfirm} />);

    selectHorse("1번 번개질주");
    fireEvent.click(screen.getByText("올인"));
    fireEvent.click(screen.getByText("베팅 확정"));

    expect(onConfirm).toHaveBeenCalledWith("horse-1", 3200);
  });

  it("잔고를 초과하는 직접 입력 시 사유 문구가 노출된다", () => {
    render(<BetPanel horses={HORSES} balance={300} onConfirm={vi.fn()} />);

    selectHorse("1번 번개질주");
    setDirectAmount("500");

    expect(screen.getByRole("alert").textContent).toBe("잔고 초과");
  });

  it("프리셋 버튼으로 금액을 설정할 수 있다", () => {
    const onConfirm = vi.fn();
    render(<BetPanel horses={HORSES} balance={10000} onConfirm={onConfirm} />);

    selectHorse("1번 번개질주");
    fireEvent.click(screen.getByText("1,000"));
    fireEvent.click(screen.getByText("베팅 확정"));

    expect(onConfirm).toHaveBeenCalledWith("horse-1", 1000);
  });

  it("잔고보다 큰 프리셋 버튼은 비활성화된다", () => {
    render(<BetPanel horses={HORSES} balance={300} onConfirm={vi.fn()} />);

    expect(isDisabled("1,000")).toBe(true);
    expect(isDisabled("500")).toBe(true);
    expect(isDisabled("100")).toBe(false);
  });

  // T18 REVIEW 이월 메모 해소(T20c): 미입력·소수 입력 경로를 값으로 고정한다.
  it("금액 미입력(amount===null) 상태에서는 role=alert 검증 메시지가 노출되지 않는다", () => {
    render(<BetPanel horses={HORSES} balance={10000} onConfirm={vi.fn()} />);

    selectHorse("1번 번개질주");

    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("type=number 직접 입력에 소수(예: 100.5)를 입력하면 정수 아님 사유가 노출된다", () => {
    render(<BetPanel horses={HORSES} balance={10000} onConfirm={vi.fn()} />);

    selectHorse("1번 번개질주");
    setDirectAmount("100.5");

    expect(screen.getByRole("alert").textContent).toBe("정수 아님");
  });
});
