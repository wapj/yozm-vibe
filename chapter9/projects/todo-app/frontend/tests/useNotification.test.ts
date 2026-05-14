import { renderHook, act } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { useNotification } from "../src/hooks/useNotification";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("useNotification", () => {
  it("granted permission 시 new Notification이 호출되고 fallback은 미호출", () => {
    const MockNotificationCtor = vi.fn() as any;
    MockNotificationCtor.permission = "granted";
    MockNotificationCtor.requestPermission = vi.fn();
    vi.stubGlobal("Notification", MockNotificationCtor);

    const { result } = renderHook(() => useNotification());
    const fallback = vi.fn();
    result.current.notify("t", "b", fallback);

    expect(MockNotificationCtor).toHaveBeenCalledTimes(1);
    expect(MockNotificationCtor).toHaveBeenCalledWith("t", { body: "b" });
    expect(fallback).not.toHaveBeenCalled();
  });

  it("denied permission 시 fallback이 호출되고 Notification 인스턴스화 없음", () => {
    const MockNotificationCtor = vi.fn() as any;
    MockNotificationCtor.permission = "denied";
    MockNotificationCtor.requestPermission = vi.fn();
    vi.stubGlobal("Notification", MockNotificationCtor);

    const { result } = renderHook(() => useNotification());
    const fallback = vi.fn();
    result.current.notify("t", "b", fallback);

    expect(MockNotificationCtor).not.toHaveBeenCalled();
    expect(fallback).toHaveBeenCalledTimes(1);
    expect(fallback).toHaveBeenCalledWith("b");
  });

  it("Notification 미정의 시 fallback이 호출된다", () => {
    vi.stubGlobal("Notification", undefined);

    const { result } = renderHook(() => useNotification());
    const fallback = vi.fn();
    result.current.notify("t", "b", fallback);

    expect(fallback).toHaveBeenCalledTimes(1);
    expect(fallback).toHaveBeenCalledWith("b");
  });

  it("requestPermission 호출 후 permission state가 granted로 갱신된다", async () => {
    const MockNotificationCtor = vi.fn() as any;
    MockNotificationCtor.permission = "default";
    MockNotificationCtor.requestPermission = vi.fn().mockResolvedValue("granted");
    vi.stubGlobal("Notification", MockNotificationCtor);

    const { result } = renderHook(() => useNotification());
    expect(result.current.permission).toBe("default");

    await act(async () => {
      await result.current.requestPermission();
    });

    expect(result.current.permission).toBe("granted");
  });
});
