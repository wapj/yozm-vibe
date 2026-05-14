import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  getActivePomodoro,
  startPomodoro,
  endPomodoro,
  discardPomodoro,
  getNextPhase,
  type PomodoroSession,
} from "../src/api/pomodoros";

const sampleSession: PomodoroSession = {
  id: 1,
  task_id: 2,
  phase: "focus",
  started_at: "2026-05-05T12:00:00Z",
  planned_duration_sec: 1500,
  ended_at: null,
  end_reason: null,
};

describe("pomodoros API", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("getActivePomodoro — 200 응답: 객체를 반환하고 /api/pomodoros/active GET 호출", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => sampleSession,
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getActivePomodoro();

    expect(result).toEqual(sampleSession);
    expect(fetchMock.mock.calls[0][0]).toBe("/api/pomodoros/active");
    expect(fetchMock.mock.calls[0][1]).toBeUndefined();
  });

  it("getActivePomodoro — 404 응답: null을 반환하고 throw 없음", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 404 })
    );

    const result = await getActivePomodoro();

    expect(result).toBeNull();
  });

  it("getActivePomodoro — 500 응답: Error를 throw", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 500 })
    );

    await expect(getActivePomodoro()).rejects.toThrow(
      "failed to load active pomodoro"
    );
  });

  it("startPomodoro — /api/pomodoros POST, JSON 헤더, 정확한 body, 응답 객체 반환", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 201,
        json: async () => sampleSession,
      })
    );

    const input = {
      task_id: 2,
      phase: "focus" as const,
      planned_duration_sec: 1500,
    };
    const result = await startPomodoro(input);

    expect(result).toEqual(sampleSession);
    expect(fetch).toHaveBeenCalledWith("/api/pomodoros", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
  });

  it("getNextPhase — 200 응답: 객체를 반환하고 /api/pomodoros/next-phase GET 호출", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ phase: "short_break", planned_duration_sec: 300 }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getNextPhase();

    expect(result).toEqual({ phase: "short_break", planned_duration_sec: 300 });
    expect(fetchMock).toHaveBeenCalledWith("/api/pomodoros/next-phase");
  });

  it("getNextPhase — 500 응답: 'failed to load next phase' throw", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 500 })
    );

    await expect(getNextPhase()).rejects.toThrow("failed to load next phase");
  });

  it("endPomodoro + discardPomodoro — 올바른 URL과 body로 POST", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => sampleSession,
    });
    vi.stubGlobal("fetch", fetchMock);

    await endPomodoro(7);
    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/pomodoros/7/end", {
      method: "POST",
    });

    await discardPomodoro(7, "discarded");
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/pomodoros/7/discard", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ end_reason: "discarded" }),
    });
  });
});
