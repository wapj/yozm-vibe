import { render, screen, act } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import PomodoroTimer from "../src/features/pomodoro/PomodoroTimer";

const baseSession = {
  id: 1,
  task_id: 1,
  phase: "focus" as const,
  started_at: "2026-05-05T12:00:00Z",
  planned_duration_sec: 1500,
  ended_at: null,
  end_reason: null,
};

const startTime = Date.parse("2026-05-05T12:00:00Z");

describe("PomodoroTimer", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("세션 시작 시점에 25:00을 표시하고 progress는 0이다", () => {
    vi.setSystemTime(startTime);
    render(<PomodoroTimer session={baseSession} />);
    expect(screen.getByTestId("pomodoro-time").textContent).toBe("25:00");
    expect((screen.getByTestId("pomodoro-progress") as HTMLProgressElement).value).toBe(0);
  });

  it("60초 경과 후 24:00을 표시하고 progress는 4이다", () => {
    vi.setSystemTime(startTime + 60000);
    render(<PomodoroTimer session={baseSession} />);
    expect(screen.getByTestId("pomodoro-time").textContent).toBe("24:00");
    expect((screen.getByTestId("pomodoro-progress") as HTMLProgressElement).value).toBe(4);
  });

  it("1500초 이상 경과 시 00:00을 표시하고 progress는 100이다", () => {
    vi.setSystemTime(startTime + 1500000);
    render(<PomodoroTimer session={baseSession} />);
    expect(screen.getByTestId("pomodoro-time").textContent).toBe("00:00");
    expect((screen.getByTestId("pomodoro-progress") as HTMLProgressElement).value).toBe(100);
  });

  it("remaining <= 0 시 onExpire가 정확히 1회 호출된다(추가 tick에도 1회)", async () => {
    const onExpire = vi.fn();
    const shortSession = { ...baseSession, planned_duration_sec: 2 };

    vi.setSystemTime(startTime);
    render(<PomodoroTimer session={shortSession} onExpire={onExpire} />);

    await act(async () => {
      vi.advanceTimersByTime(1000); // 1초 경과, remaining=1, 미만료
    });
    expect(onExpire).not.toHaveBeenCalled();

    await act(async () => {
      vi.advanceTimersByTime(2000); // 3초 경과, remaining=0, 만료
    });
    expect(onExpire).toHaveBeenCalledTimes(1);

    await act(async () => {
      vi.advanceTimersByTime(3000); // 추가 경과
    });
    expect(onExpire).toHaveBeenCalledTimes(1); // 여전히 1회
  });
});
