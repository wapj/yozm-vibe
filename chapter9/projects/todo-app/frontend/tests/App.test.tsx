import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";
import App from "../src/App";

const activeTask = {
  id: 1,
  title: "Active Task",
  note: null,
  priority: "normal",
  status: "active",
  tags: [],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  completed_at: null,
};

const doneTask = {
  id: 2,
  title: "Done Task",
  note: null,
  priority: "normal",
  status: "done",
  tags: [],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  completed_at: "2026-01-02T00:00:00Z",
};

const activeSession = {
  id: 3,
  task_id: 1,
  phase: "focus",
  started_at: new Date(Date.now() - 60_000).toISOString(), // 1분 전 (만료 아님)
  planned_duration_sec: 1500,
  ended_at: null,
  end_reason: null,
};

// /api/pomodoros/active 를 404로, 나머지 URL은 tasksResponse로 처리하는 URL-분기 mock
function makeTasksMock(tasksResponse: object) {
  return vi.fn().mockImplementation((url: string) => {
    if (url === "/api/pomodoros/active") {
      return Promise.resolve({ ok: false, status: 404 });
    }
    return Promise.resolve(tasksResponse);
  });
}

describe("App", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.unstubAllGlobals();
  });

  it("renders task list when fetch succeeds", async () => {
    const fetchMock = makeTasksMock({
      ok: true,
      json: async () => [
        {
          id: 1,
          title: "Demo",
          note: null,
          priority: "normal",
          status: "active",
          tags: [],
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
          completed_at: null,
        },
      ],
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    expect(await screen.findByTestId("task-1")).toBeInTheDocument();
    expect(await screen.findByText("Demo")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/tasks?status=active");
  });

  it("renders error message when fetch returns ok: false", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        if (url === "/api/pomodoros/active") {
          return Promise.resolve({ ok: false, status: 404 });
        }
        return Promise.resolve({ ok: false, status: 500 });
      })
    );

    render(<App />);

    expect(await screen.findByTestId("task-error")).toBeInTheDocument();
  });

  it("에러 텍스트에 'Error:' prefix가 한 번만 붙는다", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        if (url === "/api/pomodoros/active") {
          return Promise.resolve({ ok: false, status: 404 });
        }
        return Promise.resolve({ ok: false, status: 500 });
      })
    );

    render(<App />);

    const el = await screen.findByTestId("task-error");
    expect(el.textContent).toBe("Error: failed to load tasks");
  });

  it("done 항목은 기본적으로 숨겨지고 active만 표시된다", async () => {
    vi.stubGlobal(
      "fetch",
      makeTasksMock({ ok: true, json: async () => [activeTask] })
    );

    render(<App />);

    expect(await screen.findByTestId("task-1")).toBeInTheDocument();
    expect(screen.queryByTestId("task-2")).not.toBeInTheDocument();
  });

  it("완료된 항목 보기 체크박스 클릭 후 done 항목이 표시된다", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => [activeTask] })  // tasks initial
      .mockResolvedValueOnce({ ok: false, status: 404 })                     // pomodoros/active → null
      .mockResolvedValueOnce({ ok: true, json: async () => [activeTask, doneTask] });  // tasks after toggle

    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByTestId("task-1");

    await user.click(screen.getByTestId("toggle-show-completed"));

    expect(await screen.findByTestId("task-2")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenNthCalledWith(3, "/api/tasks");
  });

  it("토글 클릭 시 PATCH 요청이 전송되고 목록이 갱신된다", async () => {
    const user = userEvent.setup();
    const updatedTask = { ...activeTask, status: "done", completed_at: "2026-01-02T00:00:00Z" };

    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => [activeTask] })  // tasks initial
      .mockResolvedValueOnce({ ok: false, status: 404 })                    // pomodoros/active → null
      .mockResolvedValueOnce({ ok: true, json: async () => updatedTask });   // PATCH response

    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByTestId("task-1");

    await user.click(screen.getByTestId("task-toggle-1"));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/tasks/1",
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ status: "done" }),
      })
    );

    expect(await screen.findByTestId("task-1")).toHaveTextContent("done");
  });

  it("삭제 클릭 시 DELETE 요청이 전송되고 해당 항목이 목록에서 제거된다", async () => {
    const user = userEvent.setup();

    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => [activeTask] })  // tasks initial
      .mockResolvedValueOnce({ ok: false, status: 404 })                    // pomodoros/active → null
      .mockResolvedValueOnce({ ok: true });                                  // DELETE response

    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByTestId("task-1");

    await user.click(screen.getByTestId("task-delete-1"));

    expect(fetchMock).toHaveBeenCalledWith("/api/tasks/1", { method: "DELETE" });
    expect(screen.queryByTestId("task-1")).not.toBeInTheDocument();
  });

  it("편집 → 저장 클릭 시 PATCH가 호출되고 카드 제목이 갱신된다", async () => {
    const user = userEvent.setup();
    const updatedTask = { ...activeTask, title: "Updated Title" };

    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => [activeTask] })   // tasks initial
      .mockResolvedValueOnce({ ok: false, status: 404 })                     // pomodoros/active → null
      .mockResolvedValueOnce({ ok: true, json: async () => updatedTask });    // PATCH response

    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByTestId("task-1");

    await user.click(screen.getByTestId("task-edit-1"));
    const titleInput = screen.getByTestId("edit-title-1");
    await user.clear(titleInput);
    await user.type(titleInput, "Updated Title");
    await user.click(screen.getByTestId("task-save-1"));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/tasks/1",
      expect.objectContaining({
        method: "PATCH",
        body: expect.stringContaining("Updated Title"),
      })
    );
    expect(await screen.findByText("Updated Title")).toBeInTheDocument();
  });

  it("PATCH 실패 시 task-error 토스트가 표시되고 편집 모드가 유지된다", async () => {
    const user = userEvent.setup();

    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => [activeTask] })  // tasks initial
      .mockResolvedValueOnce({ ok: false, status: 404 })                    // pomodoros/active → null
      .mockResolvedValueOnce({ ok: false, status: 500 });                   // PATCH failure

    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByTestId("task-1");

    await user.click(screen.getByTestId("task-edit-1"));
    await user.click(screen.getByTestId("task-save-1"));

    expect(await screen.findByTestId("task-error")).toBeInTheDocument();
    expect(screen.getByTestId("task-save-1")).toBeInTheDocument();
  });

  it("검색바 입력 시 fetch가 q 파라미터를 포함한 URL로 재호출된다", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: false, status: 404 });
      }
      return Promise.resolve({ ok: true, json: async () => [activeTask] });
    });

    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByTestId("task-1");

    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/tasks?status=active");

    await user.type(screen.getByTestId("filter-q"), "a");

    await screen.findByTestId("task-1");
    const calls = fetchMock.mock.calls.map((c) => c[0] as string);
    expect(calls.some((url) => url.includes("q=a"))).toBe(true);
  });

  it("토글을 두 번 연속 클릭 시 fetch가 4회 호출되고 마지막 URL이 ?status=active", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: false, status: 404 });
      }
      return Promise.resolve({ ok: true, json: async () => [activeTask] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByTestId("task-1");

    await user.click(screen.getByTestId("toggle-show-completed")); // off→on
    await user.click(screen.getByTestId("toggle-show-completed")); // on→off

    await screen.findByTestId("task-1"); // 마지막 fetch 완료 대기

    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(fetchMock).toHaveBeenNthCalledWith(4, "/api/tasks?status=active");
  });

  it("마운트 시 활성 세션이 있으면 active-pomodoro-banner가 렌더된다", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: true, json: async () => activeSession });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    const banner = await screen.findByTestId("active-pomodoro-banner");
    expect(banner).toBeInTheDocument();
    expect(banner.textContent).toContain("활성 세션 #3");
    expect(banner.textContent).toContain("task=1");
    expect(banner.textContent).toContain("phase=focus");
  });

  it("시작 버튼 클릭 시 POST /api/pomodoros가 호출되고 배너와 타이머가 렌더된다", async () => {
    const user = userEvent.setup();

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: false, status: 404 });
      }
      if (url === "/api/pomodoros" && options?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => activeSession });
      }
      return Promise.resolve({ ok: true, json: async () => [activeTask] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByTestId("task-1");

    await user.click(screen.getByTestId("task-start-1"));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/pomodoros",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining('"task_id":1'),
      })
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/pomodoros",
      expect.objectContaining({
        body: expect.stringContaining('"phase":"focus"'),
      })
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/pomodoros",
      expect.objectContaining({
        body: expect.stringContaining('"planned_duration_sec":1500'),
      })
    );

    const banner = await screen.findByTestId("active-pomodoro-banner");
    expect(banner).toBeInTheDocument();
    expect(banner.textContent).toContain("활성 세션 #3");

    const timeEl = await screen.findByTestId("pomodoro-time");
    expect(timeEl.textContent).toMatch(/^\d{2}:\d{2}$/);
  });

  it("마운트 시 활성 세션이 없으면(404) active-pomodoro-banner가 렌더되지 않는다", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: false, status: 404 });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await waitFor(() => {
      expect(screen.queryByTestId("task-loading")).not.toBeInTheDocument();
    });

    expect(screen.queryByTestId("active-pomodoro-banner")).not.toBeInTheDocument();
  });

  it("충돌 → 완료: 409 후 다이얼로그 표시, complete 클릭 시 신규 세션으로 배너 교체", async () => {
    const user = userEvent.setup();
    const now = Date.now();
    const conflictSess = { id: 10, task_id: 2, phase: "focus" as const, started_at: new Date(now - 60_000).toISOString(), planned_duration_sec: 1500, ended_at: null, end_reason: null };
    const newSess = { id: 11, task_id: 1, phase: "focus" as const, started_at: new Date(now - 30_000).toISOString(), planned_duration_sec: 1500, ended_at: null, end_reason: null };
    let postPomodoroCount = 0;

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: true, json: async () => conflictSess });
      }
      if (url === "/api/pomodoros" && options?.method === "POST") {
        postPomodoroCount++;
        if (postPomodoroCount === 1) return Promise.resolve({ ok: false, status: 409 });
        return Promise.resolve({ ok: true, json: async () => newSess });
      }
      if (url === `/api/pomodoros/${conflictSess.id}/end` && options?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => ({ ...conflictSess, ended_at: "2026-05-05T12:25:00Z", end_reason: "completed" }) });
      }
      return Promise.resolve({ ok: true, json: async () => [activeTask] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByTestId("task-1");

    const banner = await screen.findByTestId("active-pomodoro-banner");
    expect(banner.textContent).toContain("task=2");

    await user.click(screen.getByTestId("task-start-1"));

    expect(await screen.findByTestId("pomodoro-conflict-dialog")).toBeInTheDocument();

    await user.click(screen.getByTestId("conflict-complete"));

    await waitFor(() => {
      expect(screen.queryByTestId("pomodoro-conflict-dialog")).not.toBeInTheDocument();
    });

    expect(fetchMock).toHaveBeenCalledWith(
      `/api/pomodoros/${conflictSess.id}/end`,
      expect.objectContaining({ method: "POST" })
    );

    const updatedBanner = screen.getByTestId("active-pomodoro-banner");
    expect(updatedBanner.textContent).toContain("task=1");
  });

  it("마운트 시 만료된 활성 세션 → endPomodoro 자동 호출 + 배너 미표시", async () => {
    const now = Date.now();
    const expiredSession = {
      id: 20,
      task_id: 1,
      phase: "focus" as const,
      started_at: new Date(now - 31 * 60 * 1000).toISOString(), // 31분 전 (25분 초과, 만료)
      planned_duration_sec: 1500,
      ended_at: null,
      end_reason: null,
    };

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: true, json: async () => expiredSession });
      }
      if (url === `/api/pomodoros/${expiredSession.id}/end` && options?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => ({ ...expiredSession, ended_at: new Date().toISOString(), end_reason: "completed" }) });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/pomodoros/${expiredSession.id}/end`,
        expect.objectContaining({ method: "POST" })
      );
    });

    expect(screen.queryByTestId("active-pomodoro-banner")).toBeNull();
  });

  it("진행 중 만료 시 onExpire → endPomodoro 호출 + 배너 unmount", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    const fakeNow = Date.parse("2026-05-06T10:00:00Z");
    vi.setSystemTime(fakeNow);

    const inProgressSession = {
      id: 21,
      task_id: 1,
      phase: "focus" as const,
      started_at: new Date(fakeNow).toISOString(), // 방금 시작 (만료 아님)
      planned_duration_sec: 2, // 2초
      ended_at: null,
      end_reason: null,
    };

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: true, json: async () => inProgressSession });
      }
      if (url === `/api/pomodoros/${inProgressSession.id}/end` && options?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => ({ ...inProgressSession, ended_at: new Date().toISOString(), end_reason: "completed" }) });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    // setTimeout은 실제 타이머라 findByTestId 동작함
    const banner = await screen.findByTestId("active-pomodoro-banner");
    expect(banner).toBeInTheDocument();

    // setInterval(fake) 3초 진행 → remaining 0 → onExpire 발화
    await act(async () => {
      vi.advanceTimersByTime(3000);
    });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/pomodoros/${inProgressSession.id}/end`,
        expect.objectContaining({ method: "POST" })
      );
    });

    expect(screen.queryByTestId("active-pomodoro-banner")).not.toBeInTheDocument();

    vi.useRealTimers();
  });

  it("catch 블록 보강: 충돌 후 GET /active 500 실패 시 에러 표시 + 다이얼로그 없음", async () => {
    const user = userEvent.setup();
    const now = Date.now();
    const conflictSessX = {
      id: 10,
      task_id: 2,
      phase: "focus" as const,
      started_at: new Date(now - 60_000).toISOString(),
      planned_duration_sec: 1500,
      ended_at: null,
      end_reason: null,
    };
    let activeGetCount = 0;
    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") {
        activeGetCount++;
        if (activeGetCount === 1) {
          return Promise.resolve({ ok: true, json: async () => conflictSessX });
        }
        return Promise.resolve({ ok: false, status: 500 }); // 두 번째 GET 실패
      }
      if (url === "/api/pomodoros" && options?.method === "POST") {
        return Promise.resolve({ ok: false, status: 409 });
      }
      return Promise.resolve({ ok: true, json: async () => [activeTask] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByTestId("task-1");

    await user.click(screen.getByTestId("task-start-1"));

    await waitFor(() => {
      expect(screen.getByTestId("task-error")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("pomodoro-conflict-dialog")).not.toBeInTheDocument();
  });

  it("focus 만료 → short_break 자동 시작: endPomodoro → getNextPhase → startPomodoro(short_break) → 배너 교체", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    const fakeNow = Date.parse("2026-05-06T10:00:00Z");
    vi.setSystemTime(fakeNow);

    const focusSession = {
      id: 30,
      task_id: 1,
      phase: "focus" as const,
      started_at: new Date(fakeNow).toISOString(),
      planned_duration_sec: 2,
      ended_at: null,
      end_reason: null,
    };
    const breakSession = {
      id: 31,
      task_id: 1,
      phase: "short_break" as const,
      started_at: new Date(fakeNow + 3000).toISOString(),
      planned_duration_sec: 300,
      ended_at: null,
      end_reason: null,
    };

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: true, json: async () => focusSession });
      }
      if (url === `/api/pomodoros/${focusSession.id}/end` && options?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => ({ ...focusSession, ended_at: new Date().toISOString(), end_reason: "completed" }) });
      }
      if (url === "/api/pomodoros/next-phase") {
        return Promise.resolve({ ok: true, json: async () => ({ phase: "short_break", planned_duration_sec: 300 }) });
      }
      if (url === "/api/pomodoros" && options?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => breakSession });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await screen.findByTestId("active-pomodoro-banner");

    await act(async () => {
      vi.advanceTimersByTime(3000);
    });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith("/api/pomodoros/next-phase");
    });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/pomodoros",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining('"phase":"short_break"'),
        })
      );
    });

    const banner = await screen.findByTestId("active-pomodoro-banner");
    expect(banner.textContent).toContain("phase=short_break");

    vi.useRealTimers();
  });

  it("focus 만료 → long_break 자동 시작: getNextPhase 응답 long_break → 배너 교체", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    const fakeNow = Date.parse("2026-05-06T11:00:00Z");
    vi.setSystemTime(fakeNow);

    const focusSession = {
      id: 40,
      task_id: 1,
      phase: "focus" as const,
      started_at: new Date(fakeNow).toISOString(),
      planned_duration_sec: 2,
      ended_at: null,
      end_reason: null,
    };
    const longBreakSession = {
      id: 41,
      task_id: 1,
      phase: "long_break" as const,
      started_at: new Date(fakeNow + 3000).toISOString(),
      planned_duration_sec: 900,
      ended_at: null,
      end_reason: null,
    };

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: true, json: async () => focusSession });
      }
      if (url === `/api/pomodoros/${focusSession.id}/end` && options?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => ({ ...focusSession, ended_at: new Date().toISOString(), end_reason: "completed" }) });
      }
      if (url === "/api/pomodoros/next-phase") {
        return Promise.resolve({ ok: true, json: async () => ({ phase: "long_break", planned_duration_sec: 900 }) });
      }
      if (url === "/api/pomodoros" && options?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => longBreakSession });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await screen.findByTestId("active-pomodoro-banner");

    await act(async () => {
      vi.advanceTimersByTime(3000);
    });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/pomodoros",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining('"phase":"long_break"'),
        })
      );
    });

    const banner = await screen.findByTestId("active-pomodoro-banner");
    expect(banner.textContent).toContain("phase=long_break");

    vi.useRealTimers();
  });

  it("break 만료 → 자동 시작 없음: endPomodoro 호출 + getNextPhase 미호출 + 배너 unmount", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    const fakeNow = Date.parse("2026-05-06T12:00:00Z");
    vi.setSystemTime(fakeNow);

    const breakSession = {
      id: 50,
      task_id: 1,
      phase: "short_break" as const,
      started_at: new Date(fakeNow).toISOString(),
      planned_duration_sec: 2,
      ended_at: null,
      end_reason: null,
    };

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: true, json: async () => breakSession });
      }
      if (url === `/api/pomodoros/${breakSession.id}/end` && options?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => ({ ...breakSession, ended_at: new Date().toISOString(), end_reason: "completed" }) });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await screen.findByTestId("active-pomodoro-banner");

    await act(async () => {
      vi.advanceTimersByTime(3000);
    });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/pomodoros/${breakSession.id}/end`,
        expect.objectContaining({ method: "POST" })
      );
    });

    const allCalls = fetchMock.mock.calls.map((c) => c[0] as string);
    expect(allCalls.some((url) => url.includes("/next-phase"))).toBe(false);

    expect(screen.queryByTestId("active-pomodoro-banner")).not.toBeInTheDocument();

    vi.useRealTimers();
  });

  it("break 만료 → next-focus-prompt-dialog 표시 + endPomodoro 호출 + getNextPhase 미호출", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    const fakeNow = Date.parse("2026-05-06T13:00:00Z");
    vi.setSystemTime(fakeNow);

    const breakSession = {
      id: 60,
      task_id: 1,
      phase: "short_break" as const,
      started_at: new Date(fakeNow).toISOString(),
      planned_duration_sec: 2,
      ended_at: null,
      end_reason: null,
    };

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: true, json: async () => breakSession });
      }
      if (url === `/api/pomodoros/${breakSession.id}/end` && options?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => ({ ...breakSession, ended_at: new Date().toISOString(), end_reason: "completed" }) });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await screen.findByTestId("active-pomodoro-banner");

    await act(async () => {
      vi.advanceTimersByTime(3000);
    });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/pomodoros/${breakSession.id}/end`,
        expect.objectContaining({ method: "POST" })
      );
    });

    expect(await screen.findByTestId("next-focus-prompt-dialog")).toBeInTheDocument();

    const allCalls = fetchMock.mock.calls.map((c) => c[0] as string);
    expect(allCalls.some((url) => url.includes("/next-phase"))).toBe(false);

    vi.useRealTimers();
  });

  it("break 만료 다이얼로그 '예' 클릭 → getNextPhase + startPomodoro(focus) 호출 + 다이얼로그 닫힘 + 배너 교체", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    const fakeNow = Date.parse("2026-05-06T14:00:00Z");
    vi.setSystemTime(fakeNow);

    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    const breakSession = {
      id: 61,
      task_id: 1,
      phase: "short_break" as const,
      started_at: new Date(fakeNow).toISOString(),
      planned_duration_sec: 2,
      ended_at: null,
      end_reason: null,
    };
    const newFocusSession = {
      id: 62,
      task_id: 1,
      phase: "focus" as const,
      started_at: new Date(fakeNow + 5000).toISOString(),
      planned_duration_sec: 1500,
      ended_at: null,
      end_reason: null,
    };

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: true, json: async () => breakSession });
      }
      if (url === `/api/pomodoros/${breakSession.id}/end` && options?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => ({ ...breakSession, ended_at: new Date().toISOString(), end_reason: "completed" }) });
      }
      if (url === "/api/pomodoros/next-phase") {
        return Promise.resolve({ ok: true, json: async () => ({ phase: "focus", planned_duration_sec: 1500 }) });
      }
      if (url === "/api/pomodoros" && options?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => newFocusSession });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await screen.findByTestId("active-pomodoro-banner");

    await act(async () => {
      vi.advanceTimersByTime(3000);
    });

    expect(await screen.findByTestId("next-focus-prompt-dialog")).toBeInTheDocument();

    await user.click(screen.getByTestId("next-focus-yes"));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith("/api/pomodoros/next-phase");
    });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/pomodoros",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining('"phase":"focus"'),
        })
      );
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/pomodoros",
      expect.objectContaining({
        body: expect.stringContaining(`"task_id":${breakSession.task_id}`),
      })
    );

    await waitFor(() => {
      expect(screen.queryByTestId("next-focus-prompt-dialog")).not.toBeInTheDocument();
    });

    const banner = await screen.findByTestId("active-pomodoro-banner");
    expect(banner.textContent).toContain("phase=focus");

    vi.useRealTimers();
  });

  // M5-1b: 알림 통합 테스트

  it("마운트 시 requestPermission이 1회 호출된다", async () => {
    const requestPermissionMock = vi.fn().mockResolvedValue("granted");
    const MockNotification = vi.fn();
    (MockNotification as unknown as Record<string, unknown>).permission = "default";
    (MockNotification as unknown as Record<string, unknown>).requestPermission = requestPermissionMock;
    vi.stubGlobal("Notification", MockNotification);

    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url === "/api/pomodoros/active") return Promise.resolve({ ok: false, status: 404 });
      return Promise.resolve({ ok: true, json: async () => [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await waitFor(() => expect(requestPermissionMock).toHaveBeenCalledTimes(1));
  });

  it("focus 만료 → granted 시 Notification 생성 1회, 토스트 미노출", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    const fakeNow = Date.parse("2026-05-06T17:00:00Z");
    vi.setSystemTime(fakeNow);

    const notificationInstances: { title: string; options?: unknown }[] = [];
    const MockNotification = vi.fn().mockImplementation(function (title: string, options?: unknown) {
      notificationInstances.push({ title, options });
    });
    (MockNotification as unknown as Record<string, unknown>).permission = "granted";
    (MockNotification as unknown as Record<string, unknown>).requestPermission = vi.fn().mockResolvedValue("granted");
    vi.stubGlobal("Notification", MockNotification);

    const focusSession = { id: 70, task_id: 1, phase: "focus" as const, started_at: new Date(fakeNow).toISOString(), planned_duration_sec: 2, ended_at: null, end_reason: null };
    const breakSession = { id: 71, task_id: 1, phase: "short_break" as const, started_at: new Date(fakeNow + 3000).toISOString(), planned_duration_sec: 300, ended_at: null, end_reason: null };

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") return Promise.resolve({ ok: true, json: async () => focusSession });
      if (url === `/api/pomodoros/${focusSession.id}/end` && options?.method === "POST") return Promise.resolve({ ok: true, json: async () => ({ ...focusSession, ended_at: new Date().toISOString(), end_reason: "completed" }) });
      if (url === "/api/pomodoros/next-phase") return Promise.resolve({ ok: true, json: async () => ({ phase: "short_break", planned_duration_sec: 300 }) });
      if (url === "/api/pomodoros" && options?.method === "POST") return Promise.resolve({ ok: true, json: async () => breakSession });
      return Promise.resolve({ ok: true, json: async () => [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByTestId("active-pomodoro-banner");

    await act(async () => { vi.advanceTimersByTime(3000); });

    await waitFor(() => expect(notificationInstances.length).toBeGreaterThanOrEqual(1));
    expect(screen.queryByTestId("toast")).toBeNull();

    vi.useRealTimers();
  });

  it("break 만료 → granted 시 Notification 생성 1회 + next-focus-prompt-dialog 동시 노출", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    const fakeNow = Date.parse("2026-05-06T18:00:00Z");
    vi.setSystemTime(fakeNow);

    const notificationInstances: { title: string; options?: unknown }[] = [];
    const MockNotification = vi.fn().mockImplementation(function (title: string, options?: unknown) {
      notificationInstances.push({ title, options });
    });
    (MockNotification as unknown as Record<string, unknown>).permission = "granted";
    (MockNotification as unknown as Record<string, unknown>).requestPermission = vi.fn().mockResolvedValue("granted");
    vi.stubGlobal("Notification", MockNotification);

    const breakSession = { id: 80, task_id: 1, phase: "short_break" as const, started_at: new Date(fakeNow).toISOString(), planned_duration_sec: 2, ended_at: null, end_reason: null };

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") return Promise.resolve({ ok: true, json: async () => breakSession });
      if (url === `/api/pomodoros/${breakSession.id}/end` && options?.method === "POST") return Promise.resolve({ ok: true, json: async () => ({ ...breakSession, ended_at: new Date().toISOString(), end_reason: "completed" }) });
      return Promise.resolve({ ok: true, json: async () => [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByTestId("active-pomodoro-banner");

    await act(async () => { vi.advanceTimersByTime(3000); });

    await waitFor(() => expect(notificationInstances.length).toBeGreaterThanOrEqual(1));
    expect(await screen.findByTestId("next-focus-prompt-dialog")).toBeInTheDocument();

    vi.useRealTimers();
  });

  it("focus 만료 → denied 시 Notification 미생성 + 토스트 폴백 노출", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    const fakeNow = Date.parse("2026-05-06T19:00:00Z");
    vi.setSystemTime(fakeNow);

    const notificationInstances: { title: string; options?: unknown }[] = [];
    const MockNotification = vi.fn().mockImplementation(function (title: string, options?: unknown) {
      notificationInstances.push({ title, options });
    });
    (MockNotification as unknown as Record<string, unknown>).permission = "denied";
    (MockNotification as unknown as Record<string, unknown>).requestPermission = vi.fn().mockResolvedValue("denied");
    vi.stubGlobal("Notification", MockNotification);

    const focusSession = { id: 90, task_id: 1, phase: "focus" as const, started_at: new Date(fakeNow).toISOString(), planned_duration_sec: 2, ended_at: null, end_reason: null };
    const breakSession = { id: 91, task_id: 1, phase: "short_break" as const, started_at: new Date(fakeNow + 3000).toISOString(), planned_duration_sec: 300, ended_at: null, end_reason: null };

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") return Promise.resolve({ ok: true, json: async () => focusSession });
      if (url === `/api/pomodoros/${focusSession.id}/end` && options?.method === "POST") return Promise.resolve({ ok: true, json: async () => ({ ...focusSession, ended_at: new Date().toISOString(), end_reason: "completed" }) });
      if (url === "/api/pomodoros/next-phase") return Promise.resolve({ ok: true, json: async () => ({ phase: "short_break", planned_duration_sec: 300 }) });
      if (url === "/api/pomodoros" && options?.method === "POST") return Promise.resolve({ ok: true, json: async () => breakSession });
      return Promise.resolve({ ok: true, json: async () => [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByTestId("active-pomodoro-banner");

    await act(async () => { vi.advanceTimersByTime(3000); });

    expect(await screen.findByTestId("toast")).toBeInTheDocument();
    expect(notificationInstances.length).toBe(0);

    vi.useRealTimers();
  });

  it("break 만료 다이얼로그 '아니오' 클릭 → 다이얼로그 닫힘 + 추가 API 미호출 + 배너 미표시", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    const fakeNow = Date.parse("2026-05-06T15:00:00Z");
    vi.setSystemTime(fakeNow);

    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    const breakSession = {
      id: 63,
      task_id: 1,
      phase: "short_break" as const,
      started_at: new Date(fakeNow).toISOString(),
      planned_duration_sec: 2,
      ended_at: null,
      end_reason: null,
    };

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: true, json: async () => breakSession });
      }
      if (url === `/api/pomodoros/${breakSession.id}/end` && options?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => ({ ...breakSession, ended_at: new Date().toISOString(), end_reason: "completed" }) });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await screen.findByTestId("active-pomodoro-banner");

    await act(async () => {
      vi.advanceTimersByTime(3000);
    });

    expect(await screen.findByTestId("next-focus-prompt-dialog")).toBeInTheDocument();

    const callsBeforeNo = fetchMock.mock.calls.length;

    await user.click(screen.getByTestId("next-focus-no"));

    await waitFor(() => {
      expect(screen.queryByTestId("next-focus-prompt-dialog")).not.toBeInTheDocument();
    });

    expect(fetchMock.mock.calls.length).toBe(callsBeforeNo);
    expect(screen.queryByTestId("active-pomodoro-banner")).not.toBeInTheDocument();

    vi.useRealTimers();
  });

  it("focus 만료 분기 회귀: 자동 break 시작 + next-focus-prompt-dialog 미노출", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    const fakeNow = Date.parse("2026-05-06T16:00:00Z");
    vi.setSystemTime(fakeNow);

    const focusSession = {
      id: 64,
      task_id: 1,
      phase: "focus" as const,
      started_at: new Date(fakeNow).toISOString(),
      planned_duration_sec: 2,
      ended_at: null,
      end_reason: null,
    };
    const nextBreakSession = {
      id: 65,
      task_id: 1,
      phase: "short_break" as const,
      started_at: new Date(fakeNow + 3000).toISOString(),
      planned_duration_sec: 300,
      ended_at: null,
      end_reason: null,
    };

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: true, json: async () => focusSession });
      }
      if (url === `/api/pomodoros/${focusSession.id}/end` && options?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => ({ ...focusSession, ended_at: new Date().toISOString(), end_reason: "completed" }) });
      }
      if (url === "/api/pomodoros/next-phase") {
        return Promise.resolve({ ok: true, json: async () => ({ phase: "short_break", planned_duration_sec: 300 }) });
      }
      if (url === "/api/pomodoros" && options?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => nextBreakSession });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await screen.findByTestId("active-pomodoro-banner");

    await act(async () => {
      vi.advanceTimersByTime(3000);
    });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/pomodoros",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining('"phase":"short_break"'),
        })
      );
    });

    const banner = await screen.findByTestId("active-pomodoro-banner");
    expect(banner.textContent).toContain("phase=short_break");
    expect(screen.queryByTestId("next-focus-prompt-dialog")).not.toBeInTheDocument();

    vi.useRealTimers();
  });

  it("충돌 → 취소: 다이얼로그만 닫히고 기존 세션 배너 유지, 추가 API 호출 없음", async () => {
    const user = userEvent.setup();
    const now = Date.now();
    const conflictSess = { id: 10, task_id: 2, phase: "focus" as const, started_at: new Date(now - 60_000).toISOString(), planned_duration_sec: 1500, ended_at: null, end_reason: null };
    let postPomodoroCount = 0;

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/api/pomodoros/active") {
        return Promise.resolve({ ok: true, json: async () => conflictSess });
      }
      if (url === "/api/pomodoros" && options?.method === "POST") {
        postPomodoroCount++;
        if (postPomodoroCount === 1) return Promise.resolve({ ok: false, status: 409 });
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }
      return Promise.resolve({ ok: true, json: async () => [activeTask] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByTestId("task-1");

    await user.click(screen.getByTestId("task-start-1"));

    expect(await screen.findByTestId("pomodoro-conflict-dialog")).toBeInTheDocument();

    const callsBefore = fetchMock.mock.calls.length;

    await user.click(screen.getByTestId("conflict-cancel"));

    await waitFor(() => {
      expect(screen.queryByTestId("pomodoro-conflict-dialog")).not.toBeInTheDocument();
    });

    expect(fetchMock.mock.calls.length).toBe(callsBefore);

    const banner = screen.getByTestId("active-pomodoro-banner");
    expect(banner.textContent).toContain("task=2");
  });
});
