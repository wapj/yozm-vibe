import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type { HorseRaceEntry } from "../domain/types";
import { HorseCard } from "./HorseCard";

afterEach(cleanup);

function createEntry(overrides: Partial<HorseRaceEntry> = {}): HorseRaceEntry {
  return {
    horse: {
      id: "horse-1",
      number: 1,
      name: "번개질주",
      color: "#e63946",
      personality: "저돌적",
      baseStats: { speed: 88, stamina: 60, burst: 70, luck: 45 },
      skill: { id: "start-dash", name: "스타트 대시", description: "" },
    },
    currentStats: { speed: 88, stamina: 60, burst: 70, luck: 45 },
    condition: "보통",
    winProbability: 0.3,
    odds: 3.16,
    record: { racesRun: 10, wins: 4, recentResults: [1, 2, 1, 3, 1] },
    ...overrides,
  };
}

describe("HorseCard", () => {
  it("번호·이름을 함께 표시하고, 배당률을 소수점 1자리로, 최근 5경기 성적과 전적을 노출한다", () => {
    render(<HorseCard entry={createEntry()} />);

    expect(screen.getByText("1번")).toBeTruthy();
    expect(screen.getByText("번개질주")).toBeTruthy();
    expect(screen.getByText("배당률: 3.2배")).toBeTruthy();
    expect(screen.getByText("최근 5경기: 1-2-1-3-1")).toBeTruthy();
    expect(screen.getByText("전적: 10전 4승 (승률 40.0%)")).toBeTruthy();
    expect(screen.getByText("컨디션: 보통")).toBeTruthy();
  });

  it("연승 조건(연속 1위 2회 이상)을 만족하면 연승 배지를 표시한다", () => {
    const entry = createEntry({
      record: { racesRun: 5, wins: 3, recentResults: [1, 1, 2, 3, 1] },
    });
    render(<HorseCard entry={entry} />);

    expect(screen.getByText("연승")).toBeTruthy();
  });

  it("연승 조건을 만족하지 않으면 배지를 표시하지 않는다", () => {
    const entry = createEntry({
      record: { racesRun: 5, wins: 3, recentResults: [3, 1, 1, 2, 1] },
    });
    render(<HorseCard entry={entry} />);

    expect(screen.queryByText("연승")).toBeNull();
  });

  it("records 누락(빈 전적)이나 5경기 미만 전적도 예외 없이 렌더된다", () => {
    const entry = createEntry({
      record: { racesRun: 0, wins: 0, recentResults: [] },
    });

    expect(() => render(<HorseCard entry={entry} />)).not.toThrow();
    expect(screen.getByText("1번")).toBeTruthy();
    expect(screen.getByText("최근 5경기: -")).toBeTruthy();
    expect(screen.getByText("전적: 0전 0승 (승률 0.0%)")).toBeTruthy();
  });

  it("5경기 미만의 전적(예: 3경기)도 예외 없이 렌더된다", () => {
    const entry = createEntry({
      record: { racesRun: 3, wins: 1, recentResults: [2, 1, 3] },
    });
    render(<HorseCard entry={entry} />);

    expect(screen.getByText("최근 5경기: 2-1-3")).toBeTruthy();
  });
});
