import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import TaskList from "../src/features/tasks/TaskList";
import type { Task } from "../src/api/tasks";

const makeTask = (overrides: Partial<Task> & { id: number; title: string }): Task => ({
  note: null,
  priority: "normal",
  status: "active",
  tags: [],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  completed_at: null,
  ...overrides,
});

const noop = () => {};
const noopSaveEdit = vi.fn();

describe("TaskList", () => {
  it("renders empty message when tasks is empty", () => {
    render(<TaskList tasks={[]} onToggleStatus={noop} onDelete={noop} onSaveEdit={noopSaveEdit} onStartPomodoro={noop} />);
    expect(screen.getByTestId("task-empty")).toHaveTextContent("할일이 없습니다");
  });

  it("renders task cards when tasks are provided", () => {
    const tasks = [
      makeTask({ id: 1, title: "A", tags: ["work"] }),
      makeTask({ id: 2, title: "B" }),
    ];
    render(<TaskList tasks={tasks} onToggleStatus={noop} onDelete={noop} onSaveEdit={noopSaveEdit} onStartPomodoro={noop} />);

    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
    expect(screen.getByTestId("task-1")).toBeInTheDocument();
    expect(screen.getByTestId("task-2")).toBeInTheDocument();
    expect(screen.getByTestId("task-1")).toHaveTextContent("work");
  });

  it("renders toggle and delete buttons per card and calls callbacks on click", async () => {
    const user = userEvent.setup();
    const onToggleStatus = vi.fn();
    const onDelete = vi.fn();
    const tasks = [makeTask({ id: 3, title: "C" })];

    render(<TaskList tasks={tasks} onToggleStatus={onToggleStatus} onDelete={onDelete} onSaveEdit={noopSaveEdit} onStartPomodoro={noop} />);

    await user.click(screen.getByTestId("task-toggle-3"));
    expect(onToggleStatus).toHaveBeenCalledTimes(1);
    expect(onToggleStatus).toHaveBeenCalledWith(tasks[0]);

    await user.click(screen.getByTestId("task-delete-3"));
    expect(onDelete).toHaveBeenCalledTimes(1);
    expect(onDelete).toHaveBeenCalledWith(tasks[0]);
  });

  it("shows '완료' for active tasks and '되돌리기' for done tasks", () => {
    const tasks = [
      makeTask({ id: 4, title: "Active", status: "active" }),
      makeTask({ id: 5, title: "Done", status: "done" }),
    ];
    render(<TaskList tasks={tasks} onToggleStatus={noop} onDelete={noop} onSaveEdit={noopSaveEdit} onStartPomodoro={noop} />);

    expect(screen.getByTestId("task-toggle-4")).toHaveTextContent("완료");
    expect(screen.getByTestId("task-toggle-5")).toHaveTextContent("되돌리기");
  });
});
