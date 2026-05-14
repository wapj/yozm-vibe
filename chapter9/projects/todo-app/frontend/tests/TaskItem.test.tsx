import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import TaskItem from "../src/features/tasks/TaskItem";
import type { Task } from "../src/api/tasks";

const baseTask: Task = {
  id: 1,
  title: "Test Task",
  note: "some note",
  priority: "normal",
  status: "active",
  tags: ["tag1", "tag2"],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  completed_at: null,
};

describe("TaskItem", () => {
  it("보기 모드에서 제목/우선순위/상태/태그/편집·완료·삭제 버튼이 모두 보인다", () => {
    render(
      <TaskItem
        task={baseTask}
        onToggleStatus={vi.fn()}
        onDelete={vi.fn()}
        onSaveEdit={vi.fn()}
        onStartPomodoro={vi.fn()}
      />
    );
    expect(screen.getByText("Test Task")).toBeInTheDocument();
    expect(screen.getByText(/normal/)).toBeInTheDocument();
    expect(screen.getByText(/active/)).toBeInTheDocument();
    expect(screen.getByText(/tag1/)).toBeInTheDocument();
    expect(screen.getByText("🍅 ×0")).toBeInTheDocument();
    expect(screen.getByTestId("task-edit-1")).toBeInTheDocument();
    expect(screen.getByTestId("task-toggle-1")).toBeInTheDocument();
    expect(screen.getByTestId("task-delete-1")).toBeInTheDocument();
  });

  it("[편집] 클릭 시 4개 편집 필드가 노출된다", async () => {
    const user = userEvent.setup();
    render(
      <TaskItem
        task={baseTask}
        onToggleStatus={vi.fn()}
        onDelete={vi.fn()}
        onSaveEdit={vi.fn()}
        onStartPomodoro={vi.fn()}
      />
    );
    await user.click(screen.getByTestId("task-edit-1"));
    expect(screen.getByTestId("edit-title-1")).toBeInTheDocument();
    expect(screen.getByTestId("edit-note-1")).toBeInTheDocument();
    expect(screen.getByTestId("edit-priority-1")).toBeInTheDocument();
    expect(screen.getByTestId("edit-tags-1")).toBeInTheDocument();
  });

  it("title 변경 후 [저장] 클릭 시 onSaveEdit가 변경된 title로 1회 호출된다", async () => {
    const user = userEvent.setup();
    const onSaveEdit = vi.fn().mockResolvedValue(undefined);
    render(
      <TaskItem
        task={baseTask}
        onToggleStatus={vi.fn()}
        onDelete={vi.fn()}
        onSaveEdit={onSaveEdit}
      />
    );
    await user.click(screen.getByTestId("task-edit-1"));
    const titleInput = screen.getByTestId("edit-title-1");
    await user.clear(titleInput);
    await user.type(titleInput, "New Title");
    await user.click(screen.getByTestId("task-save-1"));
    expect(onSaveEdit).toHaveBeenCalledTimes(1);
    expect(onSaveEdit).toHaveBeenCalledWith(
      baseTask,
      expect.objectContaining({ title: "New Title" })
    );
  });

  it("[취소] 클릭 시 onSaveEdit 미호출 + 보기 모드로 복귀한다", async () => {
    const user = userEvent.setup();
    const onSaveEdit = vi.fn();
    render(
      <TaskItem
        task={baseTask}
        onToggleStatus={vi.fn()}
        onDelete={vi.fn()}
        onSaveEdit={onSaveEdit}
      />
    );
    await user.click(screen.getByTestId("task-edit-1"));
    expect(screen.getByTestId("task-cancel-1")).toBeInTheDocument();
    await user.click(screen.getByTestId("task-cancel-1"));
    expect(onSaveEdit).not.toHaveBeenCalled();
    expect(screen.getByTestId("task-edit-1")).toBeInTheDocument();
    expect(screen.queryByTestId("task-save-1")).not.toBeInTheDocument();
  });

  it("빈 제목으로 [저장] 클릭 시 onSaveEdit를 호출하지 않는다", async () => {
    const user = userEvent.setup();
    const onSaveEdit = vi.fn();
    render(
      <TaskItem
        task={baseTask}
        onToggleStatus={vi.fn()}
        onDelete={vi.fn()}
        onSaveEdit={onSaveEdit}
      />
    );
    await user.click(screen.getByTestId("task-edit-1"));
    await user.clear(screen.getByTestId("edit-title-1"));
    await user.click(screen.getByTestId("task-save-1"));
    expect(onSaveEdit).not.toHaveBeenCalled();
  });

  it("note를 빈 문자열로 비우고 저장 시 note: null 로 전달된다", async () => {
    const user = userEvent.setup();
    const onSaveEdit = vi.fn().mockResolvedValue(undefined);
    render(
      <TaskItem
        task={baseTask}
        onToggleStatus={vi.fn()}
        onDelete={vi.fn()}
        onSaveEdit={onSaveEdit}
      />
    );
    await user.click(screen.getByTestId("task-edit-1"));
    await user.clear(screen.getByTestId("edit-note-1"));
    await user.click(screen.getByTestId("task-save-1"));
    expect(onSaveEdit).toHaveBeenCalledWith(
      baseTask,
      expect.objectContaining({ note: null })
    );
  });
});
