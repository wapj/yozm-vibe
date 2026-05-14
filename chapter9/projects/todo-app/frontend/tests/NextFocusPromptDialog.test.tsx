import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect } from "vitest";
import { NextFocusPromptDialog } from "../src/features/pomodoro/NextFocusPromptDialog";

describe("NextFocusPromptDialog", () => {
  it("taskId 텍스트 표시 + '예' 클릭 → onYes 1회 호출 + '아니오' 클릭 → onNo 1회 호출", async () => {
    const user = userEvent.setup();
    const onYes = vi.fn();
    const onNo = vi.fn();

    render(
      <NextFocusPromptDialog taskId={42} onYes={onYes} onNo={onNo} />
    );

    expect(screen.getByTestId("next-focus-prompt-dialog")).toBeInTheDocument();
    expect(screen.getByText(/task #42/)).toBeInTheDocument();

    await user.click(screen.getByTestId("next-focus-yes"));
    expect(onYes).toHaveBeenCalledTimes(1);

    await user.click(screen.getByTestId("next-focus-no"));
    expect(onNo).toHaveBeenCalledTimes(1);
  });
});
