import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { createDefaultState } from "../persistence/schema";
import { createGameStore } from "../store/gameStore";
import { BalanceDisplay } from "./BalanceDisplay";

afterEach(cleanup);

describe("BalanceDisplay", () => {
  it("초기 잔고(10,000)와 파산 횟수(0)를 노출한다", () => {
    const store = createGameStore(createDefaultState());
    render(<BalanceDisplay store={store} />);

    expect(screen.getByText("잔고: 10,000원")).toBeTruthy();
    expect(screen.getByText("파산 횟수: 0회")).toBeTruthy();
  });

  it("파산 발생(잔고가 MIN_BET_AMOUNT 미만) 후 재충전과 파산 횟수 증가가 반영된다", () => {
    const store = createGameStore(createDefaultState());
    render(<BalanceDisplay store={store} />);

    act(() => {
      store.adjustBalance(-9950); // 10000 -> 50 (< 100) -> 파산, 10000으로 재충전
    });

    expect(screen.getByText("잔고: 10,000원")).toBeTruthy();
    expect(screen.getByText("파산 횟수: 1회")).toBeTruthy();
  });
});
