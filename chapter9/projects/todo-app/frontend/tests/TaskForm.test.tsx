import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import TaskForm from "../src/features/tasks/TaskForm";

const mockTask = {
  id: 10,
  title: "A",
  note: null,
  priority: "normal" as const,
  status: "active" as const,
  tags: ["work", "focus"],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  completed_at: null,
};

describe("TaskForm", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("정상 제출: fetch POST 호출 및 onCreated 콜백 호출", async () => {
    const onCreated = vi.fn();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockTask,
      })
    );

    render(<TaskForm onCreated={onCreated} />);

    fireEvent.change(screen.getByTestId("task-form-title"), {
      target: { value: "A" },
    });
    fireEvent.change(screen.getByTestId("task-form-tags"), {
      target: { value: "work, focus" },
    });

    fireEvent.click(screen.getByTestId("task-form-submit"));

    await waitFor(() => expect(onCreated).toHaveBeenCalledTimes(1));
    expect(onCreated).toHaveBeenCalledWith(mockTask);

    const fetchMock = vi.mocked(fetch);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/tasks");
    expect(options.method).toBe("POST");
    const body = JSON.parse(options.body as string);
    expect(body.title).toBe("A");
    expect(body.tags).toEqual(["work", "focus"]);
    expect(body.priority).toBe("normal");
  });

  it("에러 경로: fetch 실패 시 에러 메시지 렌더, onCreated 미호출", async () => {
    const onCreated = vi.fn();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
      })
    );

    render(<TaskForm onCreated={onCreated} />);

    fireEvent.change(screen.getByTestId("task-form-title"), {
      target: { value: "B" },
    });
    fireEvent.click(screen.getByTestId("task-form-submit"));

    expect(await screen.findByTestId("task-form-error")).toBeInTheDocument();
    expect(onCreated).not.toHaveBeenCalled();
  });

  it("빈 제목: submit 시 fetch 미호출", async () => {
    const onCreated = vi.fn();
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    render(<TaskForm onCreated={onCreated} />);

    fireEvent.click(screen.getByTestId("task-form-submit"));

    await waitFor(() => expect(fetchMock).not.toHaveBeenCalled());
    expect(onCreated).not.toHaveBeenCalled();
  });
});
