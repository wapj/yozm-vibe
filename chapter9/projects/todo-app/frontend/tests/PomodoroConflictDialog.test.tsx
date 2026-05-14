import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect } from "vitest";
import PomodoroConflictDialog from "../src/features/pomodoro/PomodoroConflictDialog";

const conflictSession = {
  id: 5,
  task_id: 2,
  phase: "focus" as const,
  started_at: "2026-05-05T12:00:00Z",
  planned_duration_sec: 1500,
  ended_at: null,
  end_reason: null,
};

describe("PomodoroConflictDialog", () => {
  it("pomodoro-conflict-dialog가 렌더되고 conflict 세션 요약이 표시된다", () => {
    render(
      <PomodoroConflictDialog
        conflictSession={conflictSession}
        onComplete={vi.fn()}
        onDiscard={vi.fn()}
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByTestId("pomodoro-conflict-dialog")).toBeInTheDocument();
    expect(screen.getByText(/세션 #5/)).toBeInTheDocument();
    expect(screen.getByText(/task=2/)).toBeInTheDocument();
    expect(screen.getByText(/phase=focus/)).toBeInTheDocument();
  });

  it("conflict-complete 클릭 시 onComplete가 1회 호출된다", async () => {
    const user = userEvent.setup();
    const onComplete = vi.fn();
    render(
      <PomodoroConflictDialog
        conflictSession={conflictSession}
        onComplete={onComplete}
        onDiscard={vi.fn()}
        onCancel={vi.fn()}
      />
    );
    await user.click(screen.getByTestId("conflict-complete"));
    expect(onComplete).toHaveBeenCalledTimes(1);
  });

  it("conflict-discard 클릭 시 onDiscard, conflict-cancel 클릭 시 onCancel이 각각 1회 호출된다", async () => {
    const user = userEvent.setup();
    const onDiscard = vi.fn();
    const onCancel = vi.fn();
    render(
      <PomodoroConflictDialog
        conflictSession={conflictSession}
        onComplete={vi.fn()}
        onDiscard={onDiscard}
        onCancel={onCancel}
      />
    );
    await user.click(screen.getByTestId("conflict-discard"));
    expect(onDiscard).toHaveBeenCalledTimes(1);
    await user.click(screen.getByTestId("conflict-cancel"));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
