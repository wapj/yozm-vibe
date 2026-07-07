import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { SettlementResult } from "./SettlementResult";

afterEach(cleanup);

describe("SettlementResult", () => {
  it("적중 시 적중 문구와 지급액·정산 후 잔고를 표시한다", () => {
    render(<SettlementResult won={true} payout={325} balanceAfter={10325} />);

    expect(screen.getByText("적중").textContent).toBe("적중");
    expect(screen.getByText("지급액: 325").textContent).toBe("지급액: 325");
    expect(screen.getByText("정산 후 잔고: 10,325").textContent).toBe("정산 후 잔고: 10,325");
  });

  it("미적중 시 미적중 문구와 지급액 0을 표시한다", () => {
    render(<SettlementResult won={false} payout={0} balanceAfter={9500} />);

    expect(screen.getByText("미적중").textContent).toBe("미적중");
    expect(screen.getByText("지급액: 0").textContent).toBe("지급액: 0");
    expect(screen.getByText("정산 후 잔고: 9,500").textContent).toBe("정산 후 잔고: 9,500");
  });

  it("적중과 미적중의 문구·지급액이 값으로 구분된다", () => {
    const { unmount } = render(<SettlementResult won={true} payout={325} balanceAfter={10325} />);
    expect(screen.queryByText("미적중")).toBeNull();
    unmount();

    render(<SettlementResult won={false} payout={0} balanceAfter={9500} />);
    expect(screen.queryByText("적중")).toBeNull();
  });
});
