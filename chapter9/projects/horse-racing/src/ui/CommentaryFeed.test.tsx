import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { CommentaryFeed, COMMENTARY_FEED_MAX_LINES, type CommentaryMessage } from "./CommentaryFeed";

afterEach(cleanup);

function makeMessages(count: number): CommentaryMessage[] {
  return Array.from({ length: count }, (_, index) => ({
    id: `msg-${index}`,
    text: `메시지 ${index}`,
  }));
}

describe("CommentaryFeed", () => {
  it("빈 목록에서도 예외 없이 렌더된다", () => {
    render(<CommentaryFeed messages={[]} />);
    expect(screen.getByLabelText("실황 중계").children.length).toBe(0);
  });

  it("상한을 초과하는 메시지 목록에서 최신 상한 개수만 노출한다", () => {
    const messages = makeMessages(5);
    render(<CommentaryFeed messages={messages} />);

    const items = screen.getAllByRole("listitem");
    expect(items.length).toBe(COMMENTARY_FEED_MAX_LINES);
    expect(items[items.length - 1].textContent).toBe("메시지 4");
  });

  it("최신 항목이 노출 목록에 포함된다", () => {
    const messages = makeMessages(4);
    render(<CommentaryFeed messages={messages} />);

    expect(screen.getByText("메시지 3")).toBeTruthy();
  });
});
