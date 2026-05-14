import { render, screen } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { Toast } from "../src/components/Toast";

describe("Toast", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("메시지를 렌더한다", () => {
    render(<Toast message="hi" onClose={vi.fn()} />);
    expect(screen.getByTestId("toast").textContent).toBe("hi");
  });

  it("durationMs 후 onClose가 1회 호출된다", () => {
    const onClose = vi.fn();
    render(<Toast message="test" onClose={onClose} />);
    vi.advanceTimersByTime(4000);
    expect(onClose).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(1000);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("unmount 시 setTimeout이 정리되어 onClose가 호출되지 않는다", () => {
    const onClose = vi.fn();
    const { unmount } = render(<Toast message="bye" onClose={onClose} />);
    unmount();
    vi.advanceTimersByTime(5000);
    expect(onClose).not.toHaveBeenCalled();
  });
});
