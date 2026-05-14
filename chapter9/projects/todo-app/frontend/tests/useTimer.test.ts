import { renderHook, act } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { useNow } from "../src/hooks/useTimer";

describe("useNow", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("마운트 직후 현재 시각을 반환한다", () => {
    const t0 = Date.parse("2026-05-05T12:00:00Z");
    vi.setSystemTime(t0);
    const { result } = renderHook(() => useNow());
    expect(result.current).toBe(t0);
  });

  it("1초 경과 후 갱신된 시각을 반환한다", () => {
    const t0 = Date.parse("2026-05-05T12:00:00Z");
    vi.setSystemTime(t0);
    const { result } = renderHook(() => useNow());
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(result.current).toBeGreaterThanOrEqual(t0 + 1000);
  });
});
